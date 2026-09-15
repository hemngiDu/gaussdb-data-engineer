# ETL 开发模式

DELETE+INSERT 适合可重跑且范围明确的分区/时间窗口。DELETE 和 INSERT 必须覆盖同一业务窗口；不可因为字段名为 `months` 就默认按年删除。先确认月份类型与格式，确认窗口粒度、源过滤、目标 DELETE 范围及重跑幂等性。

字段映射只接受唯一可证明来源或显式配置；多来源同名字段标记 NEED_CONFIRM。未映射字段使用 `cast(null as <target_type>)` 作为评审占位，并标记 TODO；不可把占位当完成的 ETL。

多源 JOIN 必须有显式键和基数证据。ReferenceJoin 或配置可提供键，但驱动表、LEFT/INNER、1:1/1:N、去重规则仍需评审。对 1:N JOIN 做行数放大检查。NULL 默认保持 NULL；`nvl` 仅在明确业务要求和类型兼容时采用。
