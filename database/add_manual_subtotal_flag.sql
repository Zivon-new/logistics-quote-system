-- 修复：summary 表手动小计保护
-- 问题：trg_summary_before_insert/update 触发器无条件覆盖 NEW.小计 = SUM(fees)
--       导致用户手动输入的小计在保存后被覆盖，路线查看界面显示 0
-- 解决：新增 手动小计 标志列，触发器在该列为 1 时保留用户值

-- Step 1: 新增标志列（DEFAULT 0 = 自动计算，1 = 用户手动输入）
ALTER TABLE `summary`
    ADD COLUMN `手动小计` TINYINT(1) NOT NULL DEFAULT 0
    AFTER `小计`;

-- Step 2: 修改 BEFORE INSERT 触发器 —— 手动小计=1 时跳过自动计算
DROP TRIGGER IF EXISTS `trg_summary_before_insert`;
DELIMITER ;;
CREATE TRIGGER `trg_summary_before_insert` BEFORE INSERT ON `summary` FOR EACH ROW BEGIN
    DECLARE total_fee DECIMAL(18,2);
    DECLARE route_value DECIMAL(18,2);

    SELECT r.货值
    INTO route_value
    FROM routes r
    INNER JOIN route_agents ra ON r.路线ID = ra.路线ID
    WHERE ra.代理路线ID = NEW.代理路线ID;

    -- 只有非手动时才用费用项合计覆盖小计
    IF NEW.手动小计 = 0 THEN
        SELECT COALESCE(SUM(人民币金额), 0) + COALESCE(
            (SELECT SUM(人民币金额) FROM fee_total WHERE 代理路线ID = NEW.代理路线ID), 0
        )
        INTO total_fee
        FROM fee_items
        WHERE 代理路线ID = NEW.代理路线ID;

        SET NEW.小计 = total_fee;
    END IF;
    -- 手动小计=1 时：保留 NEW.小计（即前端传入的用户值）

    -- 多档税率：保留前端已写入的税金/汇损，不覆盖
    -- 单一税率：按正确公式重算
    IF NEW.进口税率原文 IS NULL OR NEW.进口税率原文 = '' THEN
        SET NEW.税金 = COALESCE(route_value, 0) * COALESCE(NEW.税率, 0);
        SET NEW.汇损 = NEW.税金 * COALESCE(NEW.汇损率, 0);
    END IF;

    SET NEW.总计 = NEW.小计 + NEW.税金 + NEW.汇损;
END;;
DELIMITER ;

-- Step 3: 修改 BEFORE UPDATE 触发器
-- 逻辑：
--   手动小计=0         → 自动从费用项计算
--   手动小计=1 AND OLD=1 → 保护已有手动值（recompute_summary 调用时阻止覆盖）
--   手动小计=1 AND OLD=0 → 首次设置手动（upsert 写入用户值），保留 NEW.小计
DROP TRIGGER IF EXISTS `trg_summary_before_update`;
DELIMITER ;;
CREATE TRIGGER `trg_summary_before_update` BEFORE UPDATE ON `summary` FOR EACH ROW BEGIN
    DECLARE total_fee DECIMAL(18,2);
    DECLARE route_value DECIMAL(18,2);

    SELECT r.货值
    INTO route_value
    FROM routes r
    INNER JOIN route_agents ra ON r.路线ID = ra.路线ID
    WHERE ra.代理路线ID = NEW.代理路线ID;

    IF NEW.手动小计 = 0 THEN
        SELECT COALESCE(SUM(人民币金额), 0) + COALESCE(
            (SELECT SUM(人民币金额) FROM fee_total WHERE 代理路线ID = NEW.代理路线ID), 0
        )
        INTO total_fee
        FROM fee_items
        WHERE 代理路线ID = NEW.代理路线ID;
        SET NEW.小计 = total_fee;
    ELSEIF NEW.手动小计 = 1 AND OLD.手动小计 = 1 THEN
        SET NEW.小计 = OLD.小计;
    END IF;
    -- 手动小计=1 AND OLD.手动小计=0：首次 upsert，NEW.小计 已是用户值，无需改动

    IF NEW.进口税率原文 IS NULL OR NEW.进口税率原文 = '' THEN
        SET NEW.税金 = COALESCE(route_value, 0) * COALESCE(NEW.税率, 0);
        SET NEW.汇损 = NEW.税金 * COALESCE(NEW.汇损率, 0);
    END IF;

    SET NEW.总计 = NEW.小计 + NEW.税金 + NEW.汇损;
END;;
DELIMITER ;
