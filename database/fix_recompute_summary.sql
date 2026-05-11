DROP PROCEDURE IF EXISTS `recompute_summary`;

DELIMITER ;;

CREATE PROCEDURE `recompute_summary`(IN p_agent_route_id INT)
BEGIN
    DECLARE v_route_id INT DEFAULT NULL;
    DECLARE v_subtotal DECIMAL(18,2) DEFAULT 0;
    DECLARE v_tax_rate DECIMAL(10,4) DEFAULT 0;
    DECLARE v_loss_rate DECIMAL(10,6) DEFAULT 0;
    DECLARE v_existing_tax DECIMAL(18,2) DEFAULT 0;
    DECLARE v_existing_loss DECIMAL(18,2) DEFAULT 0;
    DECLARE v_import_tax_text TEXT DEFAULT NULL;
    DECLARE v_tax DECIMAL(18,2) DEFAULT 0;
    DECLARE v_loss DECIMAL(18,2) DEFAULT 0;
    DECLARE v_total DECIMAL(18,2) DEFAULT 0;
    DECLARE v_route_value DECIMAL(18,2) DEFAULT 0;

    SELECT `路线ID` INTO v_route_id
    FROM route_agents
    WHERE `代理路线ID` = p_agent_route_id
    LIMIT 1;

    -- 用 IF 包住所有逻辑，v_route_id 为 NULL 时直接跳过，不用 LEAVE
    IF v_route_id IS NOT NULL THEN

        SELECT IFNULL(`货值`, 0) INTO v_route_value
        FROM routes
        WHERE `路线ID` = v_route_id
        LIMIT 1;

        SELECT IFNULL(SUM(`人民币金额`), 0) INTO v_subtotal
        FROM (
            SELECT `人民币金额` FROM fee_items WHERE `代理路线ID` = p_agent_route_id
            UNION ALL
            SELECT `人民币金额` FROM fee_total  WHERE `代理路线ID` = p_agent_route_id
        ) combined_fees;

        SELECT
            IFNULL(`税率`, 0),
            IFNULL(`汇损率`, 0),
            `进口税率原文`,
            IFNULL(`税金`, 0),
            IFNULL(`汇损`, 0)
        INTO v_tax_rate, v_loss_rate, v_import_tax_text, v_existing_tax, v_existing_loss
        FROM summary
        WHERE `代理路线ID` = p_agent_route_id
        LIMIT 1;

        -- 多档税率：保留前端已写入的税金/汇损，只更新小计
        -- 单一税率：按正确公式重算（税金=货值×税率，汇损=税金×汇损率）
        IF v_import_tax_text IS NOT NULL AND v_import_tax_text != '' THEN
            SET v_tax  = v_existing_tax;
            SET v_loss = v_existing_loss;
        ELSE
            SET v_tax  = v_route_value * v_tax_rate;
            SET v_loss = v_tax * v_loss_rate;
        END IF;

        SET v_total = v_subtotal + v_tax + v_loss;

        IF EXISTS(SELECT 1 FROM summary WHERE `代理路线ID` = p_agent_route_id) THEN
            UPDATE summary
            SET `小计` = v_subtotal,
                `税金` = v_tax,
                `汇损` = v_loss,
                `总计` = v_total
            WHERE `代理路线ID` = p_agent_route_id;
        ELSE
            INSERT INTO summary(`代理路线ID`, `小计`, `税率`, `税金`, `汇损率`, `汇损`, `总计`)
            VALUES (p_agent_route_id, v_subtotal, v_tax_rate, v_tax, v_loss_rate, v_loss, v_total);
        END IF;

    END IF;
END;;

DELIMITER ;
