import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from pdm_to_gaussdb import gen_ddl, gen_etl, map_type, output_project, parse_pdm
from sql_linter import lint_sql
from validate_pdm_output import validate

PDM = """<o:Model>
<o:Table Id="t1"><a:Code>irpt.irpt_order</a:Code><a:Name>订单源</a:Name>
<o:Column Id="c1"><a:Code>order_id</a:Code><a:Name>订单号</a:Name><a:DataType>BIGINT</a:DataType></o:Column>
<o:Column Id="c2"><a:Code>amount</a:Code><a:Name>金额</a:Name><a:DataType>DECIMAL(20,6)</a:DataType></o:Column>
<o:Column Id="c3"><a:Code>months</a:Code><a:Name>月份</a:Name><a:DataType>VARCHAR(7)</a:DataType></o:Column>
</o:Table>
<o:Table Id="t2"><a:Code>irpt.irpt_region</a:Code><a:Name>区域源</a:Name>
<o:Column Id="c4"><a:Code>order_id</a:Code><a:Name>订单号</a:Name><a:DataType>BIGINT</a:DataType></o:Column>
</o:Table>
<o:Table Id="t3"><a:Code>dwi.dwi_order_detail</a:Code><a:Name>订单明细</a:Name>
<o:Column Id="c5"><a:Code>order_id</a:Code><a:Name>订单号</a:Name><a:DataType>BIGINT</a:DataType></o:Column>
<o:Column Id="c6"><a:Code>amount</a:Code><a:Name>金额</a:Name><a:DataType>DECIMAL(20,6)</a:DataType></o:Column>
<o:Column Id="c7"><a:Code>months</a:Code><a:Name>月份</a:Name><a:DataType>VARCHAR(7)</a:DataType></o:Column>
</o:Table>
<o:Reference><a:Code>r1</a:Code><c:ParentTable><o:Table Ref="t1"/></c:ParentTable><c:ChildTable><o:Table Ref="t3"/></c:ChildTable></o:Reference>
<o:Reference><a:Code>r2</a:Code><c:ParentTable><o:Table Ref="t2"/></c:ParentTable><c:ChildTable><o:Table Ref="t3"/></c:ChildTable>
<o:ReferenceJoin><c:ParentColumn><o:Column Ref="c4"/></c:ParentColumn><c:ChildColumn><o:Column Ref="c5"/></c:ChildColumn></o:ReferenceJoin></o:Reference>
</o:Model>"""


class V2SafetyTests(unittest.TestCase):
    def test_preserves_type_precision(self):
        self.assertEqual(map_type("BIGINT"), ("BIGINT", ""))
        self.assertEqual(map_type("DECIMAL(20,6)"), ("DECIMAL(20,6)", ""))
        self.assertIn("NEED_CONFIRM", map_type("MYSTERY")[1])
        self.assertIn("NEED_CONFIRM", map_type("")[1])

    def test_no_distribution_guess(self):
        table = {"schema": "dwi", "name": "dwi_test", "cname": "测试", "columns": [
            {"code": "id", "name": "编号", "type": "BIGINT", "type_warning": ""}]}
        draft = "\n".join(gen_ddl(table, {}))
        self.assertIn("NEED_CONFIRM", draft)
        self.assertNotIn("\nDISTRIBUTE BY HASH (id)", draft)
        approved = "\n".join(gen_ddl(table, {"tables": {"dwi.dwi_test": {
            "distribution": {"type": "hash", "keys": ["id"]}, "distribution_reason": "高基数低倾斜"}}}))
        self.assertIn("DISTRIBUTE BY HASH (id)", approved)

    def test_pdm_reference_does_not_invent_source_join(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "model.pdm"
            path.write_text(PDM, encoding="utf-8")
            by_id, _, refs = parse_pdm(path)
            draft = "\n".join(gen_etl(by_id["t3"], refs, by_id, {}))
            self.assertIn("NEED_CONFIRM", draft)
            self.assertNotIn("\nleft join irpt.irpt_region", draft)
            self.assertNotIn("\ndelete\n", draft)
            self.assertNotIn("\ninsert into dwi.dwi_order_detail", draft)
            self.assertNotIn("nvl(", draft)

    def test_approved_rules_generate_valid_sql(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "model.pdm"
            path.write_text(PDM, encoding="utf-8")
            config = {"tables": {}, "etl": {"dwi.dwi_order_detail": {
                "incremental_predicate": "months = '${var_months}'",
                "source_predicate": "t1.months = '${var_months}'",
                "mappings": {"order_id": "t1.order_id", "amount": "t1.amount", "months": "t1.months"},
                "joins": {"irpt.irpt_region": {"type": "left", "on": ["t1.order_id = t2.order_id"],
                                               "reason": "区域源按订单号唯一，缺失区域保留订单"}}}}}
            for name, key in [("irpt.irpt_order", "order_id"), ("irpt.irpt_region", "order_id"),
                              ("dwi.dwi_order_detail", "order_id")]:
                config["tables"][name] = {"distribution": {"type": "hash", "keys": [key]},
                                           "distribution_reason": "高基数低倾斜，且与主要 JOIN 键一致"}
            output = Path(folder) / "output"
            output_project(str(path), str(output), None, config)
            self.assertEqual(validate(output), [])
            etl = (output / "链路" / "dwi_order_detail.sql").read_text(encoding="utf-8")
            self.assertIn("left join irpt.irpt_region t2", etl)
            self.assertIn("delete\nfrom dwi.dwi_order_detail", etl)

    def test_linter_blocks_unscoped_delete_and_unconfirmed_rule(self):
        rules = {item.rule for item in lint_sql("delete from dwi.t;\n-- NEED_CONFIRM: 增量范围")}
        self.assertIn("DML_WITHOUT_WHERE", rules)
        self.assertIn("UNRESOLVED_RULE", rules)

    def test_no_reference_chain_fails_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "model.pdm"
            path.write_text(PDM.split("<o:Reference>")[0] + "</o:Model>", encoding="utf-8")
            output = Path(folder) / "output"
            output_project(str(path), str(output), None, {})
            self.assertTrue((output / "链路" / "NEED_CONFIRM.md").exists())
            self.assertTrue(validate(output))

    def test_distribution_key_must_exist_and_have_reason(self):
        table = {"schema": "dwi", "name": "dwi_test", "cname": "测试", "columns": [
            {"code": "id", "name": "编号", "type": "BIGINT", "type_warning": ""}]}
        wrong = {"tables": {"dwi.dwi_test": {"distribution": {"type": "hash", "keys": ["missing"]},
                                             "distribution_reason": "高基数"}}}
        self.assertIn("NEED_CONFIRM", "\n".join(gen_ddl(table, wrong)))


if __name__ == "__main__":
    unittest.main()
