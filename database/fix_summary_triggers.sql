-- 修复 summary 表的 BEFORE INSERT / BEFORE UPDATE 触发器
-- 问题：这两个触发器会拦截每次写入，用 货值*税率 强制覆盖 NEW.税金 和 NEW.汇损
-- 修复：多档税率时（进口税率原文非空）保留前端写入的税金/汇损值
--       单一税率时修正公式：汇损 = 税金 × 汇损率（原来是 货值 × 汇损率，错误）

DROP TRIGGER IF EXISTS `trg_summary_before_insert`;

DELIMITER ;;

CREATE TRIGGER `trg_summary_before_insert` BEFORE INSERT ON `summary` FOR EACH ROW BEGIN
    DECLARE total_fee DECIMAL(18,2);
    DECLARE route_value DECIMAL(18,2);

    SELECT COALESCE(SUM(人民币金额), 0) + COALESCE(
        (SELECT SUM(人民币金额) FROM fee_total WHERE 代理路线ID = NEW.代理路线ID), 0
    )
    INTO total_fee
    FROM fee_items
    WHERE 代理路线ID = NEW.代理路线ID;

    SELECT r.货值
    INTO route_value
    FROM routes r
    INNER JOIN route_agents ra ON r.路线ID = ra.路线ID
    WHERE ra.代理路线ID = NEW.代理路线ID;

    SET NEW.小计 = total_fee;

    -- 多档税率：进口税率原文非空，保留前端已计算好的税金/汇损，不覆盖
    -- 单一税率：用正确公式计算（汇损 = 税金 × 汇损率，不是 货值 × 汇损率）
    IF NEW.进口税率原文 IS NULL OR NEW.进口税率原文 = '' THEN
        SET NEW.税金 = COALESCE(route_value, 0) * COALESCE(NEW.税率, 0);
        SET NEW.汇损 = NEW.税金 * COALESCE(NEW.汇损率, 0);
    END IF;

    SET NEW.总计 = NEW.小计 + NEW.税金 + NEW.汇损;
END;;

DELIMITER ;

DROP TRIGGER IF EXISTS `trg_summary_before_update`;

DELIMITER ;;

CREATE TRIGGER `trg_summary_before_update` BEFORE UPDATE ON `summary` FOR EACH ROW BEGIN
    DECLARE total_fee DECIMAL(18,2);
    DECLARE route_value DECIMAL(18,2);

    SELECT COALESCE(SUM(人民币金额), 0) + COALESCE(
        (SELECT SUM(人民币金额) FROM fee_total WHERE 代理路线ID = NEW.代理路线ID), 0
    )
    INTO total_fee
    FROM fee_items
    WHERE 代理路线ID = NEW.代理路线ID;

    SELECT r.货值
    INTO route_value
    FROM routes r
    INNER JOIN route_agents ra ON r.路线ID = ra.路线ID
    WHERE ra.代理路线ID = NEW.代理路线ID;

    SET NEW.小计 = total_fee;

    -- 多档税率：进口税率原文非空，保留前端已计算好的税金/汇损，不覆盖
    -- 单一税率：用正确公式计算（汇损 = 税金 × 汇损率，不是 货值 × 汇损率）
    IF NEW.进口税率原文 IS NULL OR NEW.进口税率原文 = '' THEN
        SET NEW.税金 = COALESCE(route_value, 0) * COALESCE(NEW.税率, 0);
        SET NEW.汇损 = NEW.税金 * COALESCE(NEW.汇损率, 0);
    END IF;

    SET NEW.总计 = NEW.小计 + NEW.税金 + NEW.汇损;
END;;

DELIMITER ;
