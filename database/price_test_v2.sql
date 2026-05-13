/*
 Navicat MySQL Dump SQL

 Source Server         : localhost
 Source Server Type    : MySQL
 Source Server Version : 80044 (8.0.44)
 Source Host           : localhost:3306
 Source Schema         : price_test_v2

 Target Server Type    : MySQL
 Target Server Version : 80044 (8.0.44)
 File Encoding         : 65001

 Date: 12/05/2026 13:42:34
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for agent_check_history
-- ----------------------------
DROP TABLE IF EXISTS `agent_check_history`;
CREATE TABLE `agent_check_history`  (
  `查调ID` int UNSIGNED NOT NULL AUTO_INCREMENT,
  `代理商ID` int UNSIGNED NULL DEFAULT NULL COMMENT '关联 agents.代理商ID，可为NULL（查调未入库的公司）',
  `查询关键词` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户输入的公司名/关键词',
  `llm模型` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '调用的LLM模型，如 glm-4.7',
  `报告摘要` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT 'LLM生成的背调报告摘要（300字以内）',
  `完整报告` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT 'LLM生成的完整报告JSON',
  `风险评级` enum('低风险','中等风险','高风险','无法评估') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT '无法评估',
  `信息来源` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '参考的公开信息来源URL列表',
  `token消耗` int UNSIGNED NULL DEFAULT NULL,
  `查调耗时秒` decimal(6, 2) NULL DEFAULT NULL,
  `操作用户` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `创建时间` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`查调ID`) USING BTREE,
  INDEX `idx_check_keyword`(`查询关键词`(50) ASC) USING BTREE,
  INDEX `idx_check_agent`(`代理商ID` ASC) USING BTREE,
  INDEX `idx_check_time`(`创建时间` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'AI企业背调历史记录' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for agents
-- ----------------------------
DROP TABLE IF EXISTS `agents`;
CREATE TABLE `agents`  (
  `代理商ID` int UNSIGNED NOT NULL AUTO_INCREMENT,
  `代理商名称` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '公司全称（唯一索引）',
  `代理商简称` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '常用缩写/简称',
  `国家地区` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '代理商所在国家或地区',
  `主营路线` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '逗号分隔，如\"深圳-新加坡,上海-荷兰\"',
  `主营运输方式` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '海运/空运/铁路/多式联运',
  `合作状态` enum('已合作','未合作','待确认') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '已合作',
  `信用评分` tinyint UNSIGNED NULL DEFAULT NULL COMMENT '1-100，推荐引擎打分',
  `联系方式` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `备注` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `创建时间` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `更新时间` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`代理商ID`) USING BTREE,
  UNIQUE INDEX `uk_agents_name`(`代理商名称` ASC) USING BTREE,
  INDEX `idx_agents_status`(`合作状态` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 18 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '代理商主表，规范化自 route_agents.代理商' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for country_lpi
-- ----------------------------
DROP TABLE IF EXISTS `country_lpi`;
CREATE TABLE `country_lpi`  (
  `lpiID` int UNSIGNED NOT NULL AUTO_INCREMENT,
  `国家代码` char(2) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ISO 3166-1 alpha-2',
  `国家名称` varchar(60) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `国家中文名` varchar(60) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `数据年份` year NOT NULL COMMENT 'LPI调查年份',
  `LPI综合评分` decimal(4, 2) NULL DEFAULT NULL COMMENT '1-5分',
  `通关效率` decimal(4, 2) NULL DEFAULT NULL COMMENT 'Customs（海关效率）',
  `基础设施` decimal(4, 2) NULL DEFAULT NULL COMMENT 'Infrastructure',
  `国际运输` decimal(4, 2) NULL DEFAULT NULL COMMENT 'International Shipments',
  `物流能力` decimal(4, 2) NULL DEFAULT NULL COMMENT 'Logistics Competence',
  `货物追踪` decimal(4, 2) NULL DEFAULT NULL COMMENT 'Tracking & Tracing',
  `时效性` decimal(4, 2) NULL DEFAULT NULL COMMENT 'Timeliness',
  `全球排名` smallint UNSIGNED NULL DEFAULT NULL,
  `风险等级` enum('低','中低','中','中高','高') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci GENERATED ALWAYS AS ((case when (`LPI综合评分` >= 4.0) then _utf8mb4'低' when (`LPI综合评分` >= 3.5) then _utf8mb4'中低' when (`LPI综合评分` >= 3.0) then _utf8mb4'中' when (`LPI综合评分` >= 2.5) then _utf8mb4'中高' else _utf8mb4'高' end)) STORED COMMENT '基于LPI综合评分自动生成' NULL,
  `创建时间` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`lpiID`) USING BTREE,
  UNIQUE INDEX `uk_lpi_country_year`(`国家代码` ASC, `数据年份` ASC) USING BTREE,
  INDEX `idx_lpi_score`(`LPI综合评分` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 78 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '世界银行物流绩效指数（LPI），用于航线风险评估' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for fee_items
-- ----------------------------
DROP TABLE IF EXISTS `fee_items`;
CREATE TABLE `fee_items`  (
  `费用ID` bigint NOT NULL AUTO_INCREMENT,
  `代理路线ID` int NOT NULL,
  `费用类型` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `单价` decimal(18, 2) NULL DEFAULT 0.00,
  `单位` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `数量` decimal(18, 3) NULL DEFAULT 0.000,
  `最低收费` decimal(18, 2) NULL DEFAULT NULL,
  `币种` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'RMB',
  `原币金额` decimal(18, 2) NULL DEFAULT 0.00,
  `人民币金额` decimal(18, 2) NULL DEFAULT 0.00,
  `备注` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `创建时间` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`费用ID`) USING BTREE,
  INDEX `fk_fee_items_route_agents`(`代理路线ID` ASC) USING BTREE,
  CONSTRAINT `fk_fee_items_route_agents` FOREIGN KEY (`代理路线ID`) REFERENCES `route_agents` (`代理路线ID`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 482 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for fee_total
-- ----------------------------
DROP TABLE IF EXISTS `fee_total`;
CREATE TABLE `fee_total`  (
  `整单费用ID` bigint NOT NULL AUTO_INCREMENT,
  `代理路线ID` int NOT NULL,
  `费用名称` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `原币金额` decimal(18, 2) NULL DEFAULT 0.00,
  `币种` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'RMB',
  `人民币金额` decimal(18, 2) NULL DEFAULT 0.00,
  `备注` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `创建时间` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`整单费用ID`) USING BTREE,
  INDEX `fk_fee_total_route_agents`(`代理路线ID` ASC) USING BTREE,
  CONSTRAINT `fk_fee_total_route_agents` FOREIGN KEY (`代理路线ID`) REFERENCES `route_agents` (`代理路线ID`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 536 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for forex_rate
-- ----------------------------
DROP TABLE IF EXISTS `forex_rate`;
CREATE TABLE `forex_rate`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `币种` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `汇率` decimal(12, 6) NOT NULL COMMENT '1单位外币=?人民币',
  `参考日期` date NOT NULL,
  `更新时间` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_currency`(`币种` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 36 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for forex_rate_history
-- ----------------------------
DROP TABLE IF EXISTS `forex_rate_history`;
CREATE TABLE `forex_rate_history`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `币种` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `汇率` decimal(12, 6) NOT NULL COMMENT '1单位外币=?人民币',
  `参考日期` date NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_currency_date`(`币种` ASC, `参考日期` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 408 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for fuel_price_history
-- ----------------------------
DROP TABLE IF EXISTS `fuel_price_history`;
CREATE TABLE `fuel_price_history`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `收盘价` decimal(10, 4) NOT NULL COMMENT '上期所SC888收盘价，元/桶',
  `交易日期` date NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_date`(`交易日期` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 124 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for goods_details
-- ----------------------------
DROP TABLE IF EXISTS `goods_details`;
CREATE TABLE `goods_details`  (
  `货物ID` int NOT NULL AUTO_INCREMENT,
  `路线ID` int NOT NULL,
  `货物名称` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `SKU` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '产品型号',
  `HS编码` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '海关商品编码',
  `原产国` varchar(60) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '原产地国家',
  `货物大类` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '如: 电子产品/纺织品/化工品/机械设备/食品/其他',
  `是否新品` tinyint(1) NULL DEFAULT 0,
  `货物种类` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `数量` decimal(18, 3) NULL DEFAULT 0.000,
  `单价` decimal(18, 4) NULL DEFAULT 0.0000,
  `币种` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'RMB',
  `重量(/kg)` decimal(18, 3) NULL DEFAULT 0.000 COMMENT '单个货物重量,单位:千克',
  `总重量(/kg)` decimal(18, 3) NULL DEFAULT 0.000 COMMENT '数量×单重,单位:千克',
  `总价` decimal(18, 2) NULL DEFAULT 0.00,
  `备注` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `创建时间` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`货物ID`) USING BTREE,
  INDEX `fk_goods_details_routes`(`路线ID` ASC) USING BTREE,
  CONSTRAINT `fk_goods_details_routes` FOREIGN KEY (`路线ID`) REFERENCES `routes` (`路线ID`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 88 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for goods_total
-- ----------------------------
DROP TABLE IF EXISTS `goods_total`;
CREATE TABLE `goods_total`  (
  `整单货物ID` int NOT NULL AUTO_INCREMENT,
  `路线ID` int NOT NULL,
  `货物名称` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `实际重量(/kg)` decimal(18, 2) NULL DEFAULT 0.00 COMMENT '整单实际重量,单位:千克',
  `货值` decimal(18, 2) NULL DEFAULT 0.00,
  `货值币种` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'RMB',
  `总体积(/cbm)` decimal(18, 3) NULL DEFAULT 0.000 COMMENT '整单总体积,单位:立方米',
  `备注` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `创建时间` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`整单货物ID`) USING BTREE,
  INDEX `fk_goods_total_routes`(`路线ID` ASC) USING BTREE,
  CONSTRAINT `fk_goods_total_routes` FOREIGN KEY (`路线ID`) REFERENCES `routes` (`路线ID`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 89 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for import_tax_items
-- ----------------------------
DROP TABLE IF EXISTS `import_tax_items`;
CREATE TABLE `import_tax_items`  (
  `税项ID` int UNSIGNED NOT NULL AUTO_INCREMENT,
  `代理路线ID` int NOT NULL,
  `货物描述` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `HS编码` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `原产国` varchar(60) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `关税率` decimal(8, 4) NULL DEFAULT NULL,
  `增值税率` decimal(8, 4) NULL DEFAULT NULL,
  `综合税率` decimal(8, 4) NULL DEFAULT NULL,
  `税金金额` decimal(18, 2) NULL DEFAULT NULL,
  `原文` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `创建时间` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`税项ID`) USING BTREE,
  INDEX `idx_itx_agent_route`(`代理路线ID` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '进口税率明细表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for ports
-- ----------------------------
DROP TABLE IF EXISTS `ports`;
CREATE TABLE `ports`  (
  `港口ID` int UNSIGNED NOT NULL AUTO_INCREMENT,
  `UNLOCODE` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'UN/LOCODE，如 CNSZX',
  `港口名称` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '中文名称',
  `港口英文名` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `国家代码` char(2) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ISO 3166-1 alpha-2',
  `国家名称` varchar(60) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `城市` varchar(60) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `纬度` decimal(9, 6) NULL DEFAULT NULL,
  `经度` decimal(9, 6) NULL DEFAULT NULL,
  `港口类型` enum('海港','空港','内陆港','铁路港','多式联运') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '海港',
  `所属时区` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '如 Asia/Shanghai',
  `平均清关天数` decimal(4, 1) NULL DEFAULT NULL COMMENT '历史平均清关天数',
  `LPI风险等级` enum('低','中','高') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT '中' COMMENT '基于LPI综合评估',
  `备注` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `更新时间` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`港口ID`) USING BTREE,
  UNIQUE INDEX `uk_ports_unlocode`(`UNLOCODE` ASC) USING BTREE,
  INDEX `idx_ports_country`(`国家代码` ASC) USING BTREE,
  INDEX `idx_ports_type`(`港口类型` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 134 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '全球主要港口表，基于UN/LOCODE' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for route_agents
-- ----------------------------
DROP TABLE IF EXISTS `route_agents`;
CREATE TABLE `route_agents`  (
  `代理路线ID` int NOT NULL AUTO_INCREMENT,
  `路线ID` int NOT NULL,
  `代理商` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `代理商ID` int UNSIGNED NULL DEFAULT NULL COMMENT '关联 agents.代理商ID，规范化后填充',
  `运输方式` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `贸易类型` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `代理备注` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `时效` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `时效天数` smallint UNSIGNED NULL DEFAULT NULL COMMENT '从时效字段提取的数字天数，用于排序和推荐',
  `时效备注` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `不含` varchar(511) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `是否赔付` tinyint(1) NULL DEFAULT 0 COMMENT '0=否，1=是',
  `赔付内容` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `创建时间` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`代理路线ID`) USING BTREE,
  INDEX `fk_route_agents_routes`(`路线ID` ASC) USING BTREE,
  INDEX `idx_ra_agent_id`(`代理商ID` ASC) USING BTREE,
  INDEX `idx_ra_timeliness`(`时效天数` ASC) USING BTREE,
  CONSTRAINT `fk_route_agents_routes` FOREIGN KEY (`路线ID`) REFERENCES `routes` (`路线ID`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 290 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for route_attachments
-- ----------------------------
DROP TABLE IF EXISTS `route_attachments`;
CREATE TABLE `route_attachments`  (
  `attachment_id` int NOT NULL AUTO_INCREMENT,
  `route_id` int NOT NULL,
  `original_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `stored_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `file_size` int NOT NULL DEFAULT 0,
  `file_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `upload_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `uploader` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  PRIMARY KEY (`attachment_id`) USING BTREE,
  INDEX `idx_route_id`(`route_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 16 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for route_warnings
-- ----------------------------
DROP TABLE IF EXISTS `route_warnings`;
CREATE TABLE `route_warnings`  (
  `预警ID` int UNSIGNED NOT NULL AUTO_INCREMENT,
  `国家代码` char(2) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'ISO 3166-1 alpha-2，如 YE/IQ/UA',
  `国家中文名` varchar(60) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `目的地关键词` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '匹配 routes.目的地 的关键词，如 也门/Yemen',
  `风险类型` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '战争冲突/制裁封锁/港口罢工/海盗威胁/自然灾害/政治动荡',
  `风险等级` tinyint NOT NULL COMMENT '1=低 2=中 3=高',
  `预警标题` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `预警详情` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `生效日期` date NOT NULL,
  `是否有效` tinyint(1) NOT NULL DEFAULT 1,
  `来源` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'manual',
  `创建时间` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`预警ID`) USING BTREE,
  INDEX `idx_country`(`国家代码` ASC) USING BTREE,
  INDEX `idx_keyword`(`目的地关键词` ASC) USING BTREE,
  INDEX `idx_valid`(`是否有效` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 683 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '航线风险预警' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for route_warnings_archive
-- ----------------------------
DROP TABLE IF EXISTS `route_warnings_archive`;
CREATE TABLE `route_warnings_archive`  (
  `预警ID` int UNSIGNED NOT NULL AUTO_INCREMENT,
  `国家代码` char(2) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `国家中文名` varchar(60) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `目的地关键词` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `风险类型` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `风险等级` tinyint NOT NULL,
  `预警标题` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `预警详情` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `生效日期` date NOT NULL,
  `是否有效` tinyint(1) NOT NULL DEFAULT 1,
  `来源` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'ctils',
  `创建时间` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `archived_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`预警ID`) USING BTREE,
  INDEX `idx_country`(`国家代码` ASC) USING BTREE,
  INDEX `idx_date`(`生效日期` ASC) USING BTREE,
  INDEX `idx_src`(`来源` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '预警归档库' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for routes
-- ----------------------------
DROP TABLE IF EXISTS `routes`;
CREATE TABLE `routes`  (
  `路线ID` int NOT NULL AUTO_INCREMENT,
  `起始地` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `途径地` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `目的地` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `起始港口ID` int UNSIGNED NULL DEFAULT NULL COMMENT '关联 ports.港口ID',
  `目的港口ID` int UNSIGNED NULL DEFAULT NULL COMMENT '关联 ports.港口ID',
  `交易开始日期` date NULL DEFAULT NULL COMMENT '交易周期开始日期',
  `交易结束日期` date NULL DEFAULT NULL COMMENT '交易周期结束日期',
  `交易年份` year GENERATED ALWAYS AS (year(`交易开始日期`)) STORED COMMENT '虚拟列:交易年份' NULL,
  `交易月份` tinyint GENERATED ALWAYS AS (month(`交易开始日期`)) STORED COMMENT '虚拟列:交易月份' NULL,
  `实际重量(/kg)` decimal(18, 2) NULL DEFAULT 0.00 COMMENT '路线总实际重量,单位:千克',
  `计费重量(/kg)` decimal(18, 2) NULL DEFAULT NULL COMMENT '路线计费重量,单位:千克',
  `总体积(/cbm)` decimal(18, 3) NULL DEFAULT NULL COMMENT '路线总体积,单位:立方米',
  `货值` decimal(18, 2) NULL DEFAULT 0.00,
  `货值币种` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'RMB',
  `货物名称` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '汇总的货物名称列表',
  `货物大类` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '电子产品/网络设备/机械设备/耗材/其他',
  `创建时间` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`路线ID`) USING BTREE,
  INDEX `idx_start_date`(`交易开始日期` ASC) USING BTREE COMMENT '交易开始日期索引',
  INDEX `idx_end_date`(`交易结束日期` ASC) USING BTREE COMMENT '交易结束日期索引',
  INDEX `idx_year_month`(`交易年份` ASC, `交易月份` ASC) USING BTREE COMMENT '年月查询优化索引',
  INDEX `idx_origin`(`起始地` ASC) USING BTREE COMMENT '起始地索引',
  INDEX `idx_destination`(`目的地` ASC) USING BTREE COMMENT '目的地索引',
  INDEX `idx_routes_origin_port`(`起始港口ID` ASC) USING BTREE,
  INDEX `idx_routes_dest_port`(`目的港口ID` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 243 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for summary
-- ----------------------------
DROP TABLE IF EXISTS `summary`;
CREATE TABLE `summary`  (
  `汇总ID` int NOT NULL AUTO_INCREMENT,
  `代理路线ID` int NOT NULL,
  `小计` decimal(18, 2) NULL DEFAULT 0.00,
  `运费小计` decimal(18, 2) NULL DEFAULT NULL COMMENT '运费小计不含税',
  `税率` decimal(10, 4) NULL DEFAULT 0.0000,
  `进口税率原文` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '原始进口税率描述文本',
  `税金` decimal(18, 2) NULL DEFAULT 0.00,
  `税金金额` decimal(18, 2) NULL DEFAULT NULL COMMENT '实际税金金额从Excel读取',
  `汇损率` decimal(10, 6) NULL DEFAULT 0.000000,
  `汇损` decimal(18, 2) NULL DEFAULT 0.00,
  `总计` decimal(18, 2) NULL DEFAULT 0.00,
  `总计金额` decimal(18, 2) NULL DEFAULT NULL COMMENT '含税总计金额从Excel读取',
  `备注` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `创建时间` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`汇总ID`) USING BTREE,
  UNIQUE INDEX `unique_agent_route_id`(`代理路线ID` ASC) USING BTREE,
  INDEX `idx_agent_route_id`(`代理路线ID` ASC) USING BTREE,
  CONSTRAINT `fk_summary_route_agents` FOREIGN KEY (`代理路线ID`) REFERENCES `route_agents` (`代理路线ID`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 273 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `hashed_password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `full_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `is_active` tinyint(1) NULL DEFAULT NULL,
  `is_admin` tinyint(1) NULL DEFAULT NULL,
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `ix_users_username`(`username` ASC) USING BTREE,
  INDEX `ix_users_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Procedure structure for recompute_route
-- ----------------------------
DROP PROCEDURE IF EXISTS `recompute_route`;
delimiter ;;
CREATE PROCEDURE `recompute_route`(IN p_route_id INT)
BEGIN
    -- ★★★ 所有变量声明必须在BEGIN后面 ★★★
    DECLARE v_gd_weight DECIMAL(18,3) DEFAULT 0;
    DECLARE v_gt_weight DECIMAL(18,3) DEFAULT 0;
    DECLARE v_gd_value DECIMAL(18,2) DEFAULT 0;
    DECLARE v_gt_value DECIMAL(18,2) DEFAULT 0;
    DECLARE v_gt_volume DECIMAL(18,3) DEFAULT 0;
    DECLARE v_goods_names TEXT DEFAULT '';
    DECLARE v_actual_weight DECIMAL(18,2) DEFAULT 0;
    DECLARE v_billing_weight DECIMAL(18,2) DEFAULT NULL;
    
    -- 读取routes表当前的值
    DECLARE v_current_actual_weight DECIMAL(18,2) DEFAULT 0;
    DECLARE v_current_value DECIMAL(18,2) DEFAULT 0;
    DECLARE v_current_volume DECIMAL(18,3) DEFAULT 0;
    
    -- 最终要更新的值
    DECLARE v_final_value DECIMAL(18,2) DEFAULT 0;
    DECLARE v_final_volume DECIMAL(18,3) DEFAULT 0;

    -- ★ 从 goods_details 汇总
    SELECT IFNULL(SUM(`总重量(/kg)`),0), IFNULL(SUM(`总价`),0)
    INTO v_gd_weight, v_gd_value
    FROM goods_details
    WHERE `路线ID` = p_route_id;

    -- ★ 从 goods_total 汇总(包括体积)
    SELECT 
        IFNULL(SUM(`实际重量(/kg)`),0), 
        IFNULL(SUM(`货值`),0),
        IFNULL(SUM(`总体积(/cbm)`),0)
    INTO v_gt_weight, v_gt_value, v_gt_volume
    FROM goods_total
    WHERE `路线ID` = p_route_id;

    -- ★ 汇总货物名称
    SELECT GROUP_CONCAT(DISTINCT `货物名称` SEPARATOR ', ')
    INTO v_goods_names
    FROM (
        SELECT `货物名称` FROM goods_details WHERE `路线ID` = p_route_id AND `货物名称` IS NOT NULL
        UNION
        SELECT `货物名称` FROM goods_total WHERE `路线ID` = p_route_id AND `货物名称` IS NOT NULL
    ) combined_goods;

    -- 计算goods汇总后的实际重量
    SET v_actual_weight = v_gd_weight + v_gt_weight;
    
    -- ★ 读取routes表当前的值
    SELECT 
        IFNULL(`实际重量(/kg)`, 0),
        IFNULL(`计费重量(/kg)`, 0),
        IFNULL(`货值`, 0),
        IFNULL(`总体积(/cbm)`, 0)
    INTO 
        v_current_actual_weight,
        v_billing_weight,
        v_current_value,
        v_current_volume
    FROM routes
    WHERE `路线ID` = p_route_id;
    
    -- ★ 如果计费重量为NULL,使用实际重量
    IF v_billing_weight IS NULL THEN
        SET v_billing_weight = v_actual_weight;
    END IF;

    -- ★★★ 关键修复：优先保留routes表的手动值 ★★★
    -- 规则：
    -- 1. 如果goods表有数据（汇总值>0），用汇总值
    -- 2. 如果goods表无数据但routes表有手动值，保留手动值
    -- 3. 都没有则为0
    
    -- 实际重量：优先用goods汇总，没有则保留routes原值
    IF v_actual_weight > 0 THEN
        SET v_actual_weight = v_actual_weight;
    ELSE
        SET v_actual_weight = v_current_actual_weight;
    END IF;
    
    -- 货值：优先用goods汇总，没有则保留routes原值
    IF (v_gd_value + v_gt_value) > 0 THEN
        SET v_final_value = v_gd_value + v_gt_value;
    ELSE
        SET v_final_value = v_current_value;
    END IF;
    
    -- 总体积：优先用goods汇总，没有则保留routes原值
    IF v_gt_volume > 0 THEN
        SET v_final_volume = v_gt_volume;
    ELSE
        SET v_final_volume = v_current_volume;
    END IF;

    -- ★ 更新 routes 表（使用优先级后的值）
    UPDATE routes
    SET 
        `实际重量(/kg)` = v_actual_weight,
        `计费重量(/kg)` = v_billing_weight,
        `货值` = v_final_value,
        `总体积(/cbm)` = v_final_volume,
        `货物名称` = v_goods_names
    WHERE `路线ID` = p_route_id;
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for recompute_summary
-- ----------------------------
DROP PROCEDURE IF EXISTS `recompute_summary`;
delimiter ;;
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
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for recompute_summary_for_route
-- ----------------------------
DROP PROCEDURE IF EXISTS `recompute_summary_for_route`;
delimiter ;;
CREATE PROCEDURE `recompute_summary_for_route`(IN p_route_id INT)
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE v_agent_route_id INT;
    DECLARE cur_agents CURSOR FOR 
        SELECT `代理路线ID` FROM route_agents WHERE `路线ID` = p_route_id;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

    OPEN cur_agents;
    read_loop: LOOP
        FETCH cur_agents INTO v_agent_route_id;
        IF done THEN
            LEAVE read_loop;
        END IF;
        CALL recompute_summary(v_agent_route_id);
    END LOOP;
    CLOSE cur_agents;
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for sp_refresh_all_calculations
-- ----------------------------
DROP PROCEDURE IF EXISTS `sp_refresh_all_calculations`;
delimiter ;;
CREATE PROCEDURE `sp_refresh_all_calculations`()
BEGIN
    -- 刷新所有routes的货值
    UPDATE routes r
    SET r.货值 = (
        SELECT COALESCE(SUM(gd.总价), 0) + COALESCE(
            (SELECT SUM(gt.货值) FROM goods_total gt WHERE gt.路线ID = r.路线ID), 0
        )
        FROM goods_details gd
        WHERE gd.路线ID = r.路线ID
    );
    
    -- 刷新所有fee_items的数量
    UPDATE fee_items fi
    INNER JOIN route_agents ra ON fi.代理路线ID = ra.代理路线ID
    INNER JOIN routes r ON ra.路线ID = r.路线ID
    SET fi.数量 = CASE
        WHEN fi.单位 = '/kg' THEN COALESCE(r.`计费重量(/kg)`, 0)
        WHEN fi.单位 = '/cbm' THEN COALESCE(r.`总体积(/cbm)`, 0)
        ELSE 1
    END,
    fi.原币金额 = fi.单价 * fi.数量;
    
    -- 刷新所有summary的汇总
    UPDATE summary s
    SET s.小计 = (
        SELECT COALESCE(SUM(fi.人民币金额), 0) + COALESCE(
            (SELECT SUM(ft.人民币金额) FROM fee_total ft WHERE ft.代理路线ID = s.代理路线ID), 0
        )
        FROM fee_items fi
        WHERE fi.代理路线ID = s.代理路线ID
    ),
    s.税金 = s.小计 * COALESCE(s.税率, 0),
    s.汇损 = s.小计 * COALESCE(s.汇损率, 0),
    s.总计 = s.小计 + s.税金 + s.汇损;
    
    SELECT '✅ 所有计算已刷新完成' AS '结果';
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for sp_refresh_fee_items_quantity
-- ----------------------------
DROP PROCEDURE IF EXISTS `sp_refresh_fee_items_quantity`;
delimiter ;;
CREATE PROCEDURE `sp_refresh_fee_items_quantity`(IN agent_route_id INT)
BEGIN
    UPDATE fee_items fi
    INNER JOIN route_agents ra ON fi.代理路线ID = ra.代理路线ID
    INNER JOIN routes r ON ra.路线ID = r.路线ID
    SET fi.数量 = CASE
        WHEN fi.单位 = '/kg' THEN COALESCE(r.`计费重量(/kg)`, 0)
        WHEN fi.单位 = '/cbm' THEN COALESCE(r.`总体积(/cbm)`, 0)
        ELSE 1
    END,
    fi.原币金额 = fi.单价 * fi.数量
    WHERE fi.代理路线ID = agent_route_id;
    
    SELECT CONCAT('✅ 代理路线ID ', agent_route_id, ' 的费用数量已更新') AS '结果';
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for sp_refresh_rmb_amounts
-- ----------------------------
DROP PROCEDURE IF EXISTS `sp_refresh_rmb_amounts`;
delimiter ;;
CREATE PROCEDURE `sp_refresh_rmb_amounts`()
BEGIN
    -- 更新fee_items
    UPDATE fee_items fi
    LEFT JOIN forex_rate fr ON fi.币种 = fr.币种
    SET fi.人民币金额 = fi.原币金额 * COALESCE(fr.汇率, 1);
    
    -- 更新fee_total
    UPDATE fee_total ft
    LEFT JOIN forex_rate fr ON ft.币种 = fr.币种
    SET ft.人民币金额 = ft.原币金额 * COALESCE(fr.汇率, 1);
    
    SELECT '✅ 所有人民币金额已更新' AS '结果';
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for sp_refresh_route_goods_value
-- ----------------------------
DROP PROCEDURE IF EXISTS `sp_refresh_route_goods_value`;
delimiter ;;
CREATE PROCEDURE `sp_refresh_route_goods_value`(IN route_id INT)
BEGIN
    UPDATE routes r
    SET r.货值 = (
        SELECT COALESCE(SUM(gd.总价), 0) + COALESCE(
            (SELECT SUM(gt.货值) FROM goods_total gt WHERE gt.路线ID = route_id), 0
        )
        FROM goods_details gd
        WHERE gd.路线ID = route_id
    )
    WHERE r.路线ID = route_id;
    
    SELECT CONCAT('✅ 路线ID ', route_id, ' 的货值已更新') AS '结果';
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for sp_refresh_summary_totals
-- ----------------------------
DROP PROCEDURE IF EXISTS `sp_refresh_summary_totals`;
delimiter ;;
CREATE PROCEDURE `sp_refresh_summary_totals`(IN agent_route_id INT)
BEGIN
    UPDATE summary s
    SET s.小计 = (
        SELECT COALESCE(SUM(fi.人民币金额), 0) + COALESCE(
            (SELECT SUM(ft.人民币金额) FROM fee_total ft WHERE ft.代理路线ID = agent_route_id), 0
        )
        FROM fee_items fi
        WHERE fi.代理路线ID = agent_route_id
    ),
    s.税金 = s.小计 * COALESCE(s.税率, 0),
    s.汇损 = s.小计 * COALESCE(s.汇损率, 0),
    s.总计 = s.小计 + s.税金 + s.汇损
    WHERE s.代理路线ID = agent_route_id;
    
    SELECT CONCAT('✅ 代理路线ID ', agent_route_id, ' 的汇总已更新') AS '结果';
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_items
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_items_bi`;
delimiter ;;
CREATE TRIGGER `trg_fee_items_bi` BEFORE INSERT ON `fee_items` FOR EACH ROW BEGIN
    DECLARE v_rate DECIMAL(18,8) DEFAULT 1;
    
    IF NEW.`币种` IS NULL OR NEW.`币种` = '' OR UPPER(NEW.`币种`) IN ('RMB','CNY') THEN
        SET v_rate = 1;
    ELSE
        SELECT IFNULL(`汇率`,1) INTO v_rate FROM forex_rate WHERE `币种` = NEW.`币种` LIMIT 1;
    END IF;

    SET NEW.`原币金额` = IFNULL(NEW.`单价`,0) * IFNULL(NEW.`数量`,0);
    SET NEW.`人民币金额` = NEW.`原币金额` * v_rate;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_items
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_items_before_insert`;
delimiter ;;
CREATE TRIGGER `trg_fee_items_before_insert` BEFORE INSERT ON `fee_items` FOR EACH ROW BEGIN
    DECLARE route_weight DECIMAL(18,2);
    DECLARE route_volume DECIMAL(18,3);
    
    -- 获取路线的计费重量和总体积
    SELECT `计费重量(/kg)`, `总体积(/cbm)` 
    INTO route_weight, route_volume
    FROM routes r
    INNER JOIN route_agents ra ON r.路线ID = ra.路线ID
    WHERE ra.代理路线ID = NEW.代理路线ID;
    
    -- 根据单位设置数量
    IF NEW.单位 = '/kg' THEN
        SET NEW.数量 = COALESCE(route_weight, 0);
    ELSEIF NEW.单位 = '/cbm' THEN
        SET NEW.数量 = COALESCE(route_volume, 0);
    ELSEIF NEW.数量 IS NULL OR NEW.数量 = 0 THEN
        SET NEW.数量 = 1;
    END IF;
    
    -- 自动计算原币金额
    SET NEW.原币金额 = NEW.单价 * NEW.数量;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_items
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_items_calculate_rmb`;
delimiter ;;
CREATE TRIGGER `trg_fee_items_calculate_rmb` BEFORE INSERT ON `fee_items` FOR EACH ROW BEGIN
    DECLARE exchange_rate DECIMAL(18, 8);
    
    -- 获取汇率
    SELECT 汇率 INTO exchange_rate 
    FROM forex_rate 
    WHERE 币种 = NEW.币种;
    
    -- 计算人民币金额
    SET NEW.人民币金额 = NEW.原币金额 * COALESCE(exchange_rate, 1);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_items
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_items_calc_rmb_insert`;
delimiter ;;
CREATE TRIGGER `trg_fee_items_calc_rmb_insert` BEFORE INSERT ON `fee_items` FOR EACH ROW BEGIN
    DECLARE exchange_rate DECIMAL(18, 8);
    
    -- 从汇率表获取对应币种的汇率
    SELECT 汇率 INTO exchange_rate 
    FROM forex_rate 
    WHERE 币种 = NEW.币种;
    
    -- 如果找到汇率，自动计算人民币金额
    IF exchange_rate IS NOT NULL THEN
        SET NEW.人民币金额 = NEW.原币金额 * exchange_rate;
    ELSE
        -- 如果汇率表中没有该币种，默认按1:1计算
        SET NEW.人民币金额 = NEW.原币金额;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_items
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_items_ai`;
delimiter ;;
CREATE TRIGGER `trg_fee_items_ai` AFTER INSERT ON `fee_items` FOR EACH ROW BEGIN
    CALL recompute_summary(NEW.`代理路线ID`);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_items
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_items_bu`;
delimiter ;;
CREATE TRIGGER `trg_fee_items_bu` BEFORE UPDATE ON `fee_items` FOR EACH ROW BEGIN
    DECLARE v_rate DECIMAL(18,8) DEFAULT 1;
    
    IF NEW.`币种` IS NULL OR NEW.`币种` = '' OR UPPER(NEW.`币种`) IN ('RMB','CNY') THEN
        SET v_rate = 1;
    ELSE
        SELECT IFNULL(`汇率`,1) INTO v_rate FROM forex_rate WHERE `币种` = NEW.`币种` LIMIT 1;
    END IF;

    SET NEW.`原币金额` = IFNULL(NEW.`单价`,0) * IFNULL(NEW.`数量`,0);
    SET NEW.`人民币金额` = NEW.`原币金额` * v_rate;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_items
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_items_before_update`;
delimiter ;;
CREATE TRIGGER `trg_fee_items_before_update` BEFORE UPDATE ON `fee_items` FOR EACH ROW BEGIN
    DECLARE route_weight DECIMAL(18,2);
    DECLARE route_volume DECIMAL(18,3);
    
    -- 获取路线的计费重量和总体积
    SELECT `计费重量(/kg)`, `总体积(/cbm)` 
    INTO route_weight, route_volume
    FROM routes r
    INNER JOIN route_agents ra ON r.路线ID = ra.路线ID
    WHERE ra.代理路线ID = NEW.代理路线ID;
    
    -- 根据单位设置数量
    IF NEW.单位 = '/kg' THEN
        SET NEW.数量 = COALESCE(route_weight, 0);
    ELSEIF NEW.单位 = '/cbm' THEN
        SET NEW.数量 = COALESCE(route_volume, 0);
    ELSEIF NEW.数量 IS NULL OR NEW.数量 = 0 THEN
        SET NEW.数量 = 1;
    END IF;
    
    -- 自动计算原币金额
    SET NEW.原币金额 = NEW.单价 * NEW.数量;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_items
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_items_update_rmb`;
delimiter ;;
CREATE TRIGGER `trg_fee_items_update_rmb` BEFORE UPDATE ON `fee_items` FOR EACH ROW BEGIN
    DECLARE exchange_rate DECIMAL(18, 8);
    
    SELECT 汇率 INTO exchange_rate 
    FROM forex_rate 
    WHERE 币种 = NEW.币种;
    
    SET NEW.人民币金额 = NEW.原币金额 * COALESCE(exchange_rate, 1);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_items
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_items_calc_rmb_update`;
delimiter ;;
CREATE TRIGGER `trg_fee_items_calc_rmb_update` BEFORE UPDATE ON `fee_items` FOR EACH ROW BEGIN
    DECLARE exchange_rate DECIMAL(18, 8);
    
    -- 从汇率表获取对应币种的汇率
    SELECT 汇率 INTO exchange_rate 
    FROM forex_rate 
    WHERE 币种 = NEW.币种;
    
    -- 如果找到汇率，自动计算人民币金额
    IF exchange_rate IS NOT NULL THEN
        SET NEW.人民币金额 = NEW.原币金额 * exchange_rate;
    ELSE
        -- 如果汇率表中没有该币种，默认按1:1计算
        SET NEW.人民币金额 = NEW.原币金额;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_items
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_items_au`;
delimiter ;;
CREATE TRIGGER `trg_fee_items_au` AFTER UPDATE ON `fee_items` FOR EACH ROW BEGIN
    CALL recompute_summary(NEW.`代理路线ID`);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_items
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_items_ad`;
delimiter ;;
CREATE TRIGGER `trg_fee_items_ad` AFTER DELETE ON `fee_items` FOR EACH ROW BEGIN
    CALL recompute_summary(OLD.`代理路线ID`);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_total_bi`;
delimiter ;;
CREATE TRIGGER `trg_fee_total_bi` BEFORE INSERT ON `fee_total` FOR EACH ROW BEGIN
    DECLARE v_rate DECIMAL(18,8) DEFAULT 1;
    
    IF NEW.`币种` IS NULL OR NEW.`币种` = '' OR UPPER(NEW.`币种`) IN ('RMB','CNY') THEN
        SET v_rate = 1;
    ELSE
        SELECT IFNULL(`汇率`,1) INTO v_rate FROM forex_rate WHERE `币种` = NEW.`币种` LIMIT 1;
    END IF;

    SET NEW.`人民币金额` = IFNULL(NEW.`原币金额`,0) * v_rate;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_total_calculate_rmb`;
delimiter ;;
CREATE TRIGGER `trg_fee_total_calculate_rmb` BEFORE INSERT ON `fee_total` FOR EACH ROW BEGIN
    DECLARE exchange_rate DECIMAL(18, 8);
    SELECT 汇率 INTO exchange_rate FROM forex_rate WHERE 币种 = NEW.币种;
    SET NEW.人民币金额 = NEW.原币金额 * COALESCE(exchange_rate, 1);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_total_calc_rmb_insert`;
delimiter ;;
CREATE TRIGGER `trg_fee_total_calc_rmb_insert` BEFORE INSERT ON `fee_total` FOR EACH ROW BEGIN
    DECLARE exchange_rate DECIMAL(18, 8);
    
    -- 从汇率表获取对应币种的汇率
    SELECT 汇率 INTO exchange_rate 
    FROM forex_rate 
    WHERE 币种 = NEW.币种;
    
    -- 如果找到汇率，自动计算人民币金额
    IF exchange_rate IS NOT NULL THEN
        SET NEW.人民币金额 = NEW.原币金额 * exchange_rate;
    ELSE
        -- 如果汇率表中没有该币种，默认按1:1计算
        SET NEW.人民币金额 = NEW.原币金额;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_total_ai`;
delimiter ;;
CREATE TRIGGER `trg_fee_total_ai` AFTER INSERT ON `fee_total` FOR EACH ROW BEGIN
    CALL recompute_summary(NEW.`代理路线ID`);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_total_bu`;
delimiter ;;
CREATE TRIGGER `trg_fee_total_bu` BEFORE UPDATE ON `fee_total` FOR EACH ROW BEGIN
    DECLARE v_rate DECIMAL(18,8) DEFAULT 1;
    IF NEW.`币种` IS NULL OR NEW.`币种` = '' OR UPPER(NEW.`币种`) IN ('RMB','CNY') THEN
        SET v_rate = 1;
    ELSE
        SELECT IFNULL(`汇率`,1) INTO v_rate FROM forex_rate WHERE `币种` = NEW.`币种` LIMIT 1;
    END IF;

    SET NEW.`人民币金额` = IFNULL(NEW.`原币金额`,0) * v_rate;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_total_update_rmb`;
delimiter ;;
CREATE TRIGGER `trg_fee_total_update_rmb` BEFORE UPDATE ON `fee_total` FOR EACH ROW BEGIN
    DECLARE exchange_rate DECIMAL(18, 8);
    SELECT 汇率 INTO exchange_rate FROM forex_rate WHERE 币种 = NEW.币种;
    SET NEW.人民币金额 = NEW.原币金额 * COALESCE(exchange_rate, 1);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_total_calc_rmb_update`;
delimiter ;;
CREATE TRIGGER `trg_fee_total_calc_rmb_update` BEFORE UPDATE ON `fee_total` FOR EACH ROW BEGIN
    DECLARE exchange_rate DECIMAL(18, 8);
    
    -- 从汇率表获取对应币种的汇率
    SELECT 汇率 INTO exchange_rate 
    FROM forex_rate 
    WHERE 币种 = NEW.币种;
    
    -- 如果找到汇率，自动计算人民币金额
    IF exchange_rate IS NOT NULL THEN
        SET NEW.人民币金额 = NEW.原币金额 * exchange_rate;
    ELSE
        -- 如果汇率表中没有该币种，默认按1:1计算
        SET NEW.人民币金额 = NEW.原币金额;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_total_au`;
delimiter ;;
CREATE TRIGGER `trg_fee_total_au` AFTER UPDATE ON `fee_total` FOR EACH ROW BEGIN
    CALL recompute_summary(NEW.`代理路线ID`);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_total_ad`;
delimiter ;;
CREATE TRIGGER `trg_fee_total_ad` AFTER DELETE ON `fee_total` FOR EACH ROW BEGIN
    CALL recompute_summary(OLD.`代理路线ID`);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table goods_details
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_goods_details_bi`;
delimiter ;;
CREATE TRIGGER `trg_goods_details_bi` BEFORE INSERT ON `goods_details` FOR EACH ROW BEGIN
    DECLARE v_rate DECIMAL(18,8) DEFAULT 1;
    
    IF NEW.`币种` IS NULL OR NEW.`币种` = '' OR UPPER(NEW.`币种`) IN ('RMB','CNY') THEN
        SET v_rate = 1;
    ELSE
        SELECT IFNULL(`汇率`,1) INTO v_rate FROM forex_rate WHERE `币种` = NEW.`币种` LIMIT 1;
    END IF;

    SET NEW.`总重量(/kg)` = IFNULL(NEW.`数量`,0) * IFNULL(NEW.`重量(/kg)`,0);
    SET NEW.`总价` = IFNULL(NEW.`数量`,0) * IFNULL(NEW.`单价`,0) * v_rate;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table goods_details
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_goods_details_after_insert`;
delimiter ;;
CREATE TRIGGER `trg_goods_details_after_insert` AFTER INSERT ON `goods_details` FOR EACH ROW BEGIN
    UPDATE routes r
    SET r.货值 = (
        SELECT COALESCE(SUM(gd.总价), 0) + COALESCE(
            (SELECT SUM(gt.货值) FROM goods_total gt WHERE gt.路线ID = NEW.路线ID), 0
        )
        FROM goods_details gd
        WHERE gd.路线ID = NEW.路线ID
    )
    WHERE r.路线ID = NEW.路线ID;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table goods_details
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_goods_details_au`;
delimiter ;;
CREATE TRIGGER `trg_goods_details_au` AFTER UPDATE ON `goods_details` FOR EACH ROW BEGIN
    CALL recompute_route(NEW.`路线ID`);
    CALL recompute_summary_for_route(NEW.`路线ID`);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table goods_details
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_goods_details_after_update`;
delimiter ;;
CREATE TRIGGER `trg_goods_details_after_update` AFTER UPDATE ON `goods_details` FOR EACH ROW BEGIN
    UPDATE routes r
    SET r.货值 = (
        SELECT COALESCE(SUM(gd.总价), 0) + COALESCE(
            (SELECT SUM(gt.货值) FROM goods_total gt WHERE gt.路线ID = NEW.路线ID), 0
        )
        FROM goods_details gd
        WHERE gd.路线ID = NEW.路线ID
    )
    WHERE r.路线ID = NEW.路线ID;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table goods_details
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_goods_details_ad`;
delimiter ;;
CREATE TRIGGER `trg_goods_details_ad` AFTER DELETE ON `goods_details` FOR EACH ROW BEGIN
    CALL recompute_route(OLD.`路线ID`);
    CALL recompute_summary_for_route(OLD.`路线ID`);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table goods_details
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_goods_details_after_delete`;
delimiter ;;
CREATE TRIGGER `trg_goods_details_after_delete` AFTER DELETE ON `goods_details` FOR EACH ROW BEGIN
    UPDATE routes r
    SET r.货值 = (
        SELECT COALESCE(SUM(gd.总价), 0) + COALESCE(
            (SELECT SUM(gt.货值) FROM goods_total gt WHERE gt.路线ID = OLD.路线ID), 0
        )
        FROM goods_details gd
        WHERE gd.路线ID = OLD.路线ID
    )
    WHERE r.路线ID = OLD.路线ID;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table goods_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_goods_total_bi`;
delimiter ;;
CREATE TRIGGER `trg_goods_total_bi` BEFORE INSERT ON `goods_total` FOR EACH ROW BEGIN
    IF NEW.`货值` IS NULL THEN
        SET NEW.`货值` = 0;
    END IF;
    IF NEW.`实际重量(/kg)` IS NULL THEN
        SET NEW.`实际重量(/kg)` = 0;
    END IF;
    IF NEW.`总体积(/cbm)` IS NULL THEN
        SET NEW.`总体积(/cbm)` = 0;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table goods_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_goods_total_ai`;
delimiter ;;
CREATE TRIGGER `trg_goods_total_ai` AFTER INSERT ON `goods_total` FOR EACH ROW BEGIN
    CALL recompute_route(NEW.`路线ID`);
    CALL recompute_summary_for_route(NEW.`路线ID`);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table goods_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_goods_total_after_insert`;
delimiter ;;
CREATE TRIGGER `trg_goods_total_after_insert` AFTER INSERT ON `goods_total` FOR EACH ROW BEGIN
    UPDATE routes r
    SET r.货值 = (
        SELECT COALESCE(SUM(gt.货值), 0) + COALESCE(
            (SELECT SUM(gd.总价) FROM goods_details gd WHERE gd.路线ID = NEW.路线ID), 0
        )
        FROM goods_total gt
        WHERE gt.路线ID = NEW.路线ID
    )
    WHERE r.路线ID = NEW.路线ID;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table goods_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_goods_total_bu`;
delimiter ;;
CREATE TRIGGER `trg_goods_total_bu` BEFORE UPDATE ON `goods_total` FOR EACH ROW BEGIN
    IF NEW.`货值` IS NULL THEN
        SET NEW.`货值` = 0;
    END IF;
    IF NEW.`实际重量(/kg)` IS NULL THEN
        SET NEW.`实际重量(/kg)` = 0;
    END IF;
    IF NEW.`总体积(/cbm)` IS NULL THEN
        SET NEW.`总体积(/cbm)` = 0;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table goods_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_goods_total_au`;
delimiter ;;
CREATE TRIGGER `trg_goods_total_au` AFTER UPDATE ON `goods_total` FOR EACH ROW BEGIN
    CALL recompute_route(NEW.`路线ID`);
    CALL recompute_summary_for_route(NEW.`路线ID`);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table goods_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_goods_total_after_update`;
delimiter ;;
CREATE TRIGGER `trg_goods_total_after_update` AFTER UPDATE ON `goods_total` FOR EACH ROW BEGIN
    UPDATE routes r
    SET r.货值 = (
        SELECT COALESCE(SUM(gt.货值), 0) + COALESCE(
            (SELECT SUM(gd.总价) FROM goods_details gd WHERE gd.路线ID = NEW.路线ID), 0
        )
        FROM goods_total gt
        WHERE gt.路线ID = NEW.路线ID
    )
    WHERE r.路线ID = NEW.路线ID;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table goods_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_goods_total_ad`;
delimiter ;;
CREATE TRIGGER `trg_goods_total_ad` AFTER DELETE ON `goods_total` FOR EACH ROW BEGIN
    CALL recompute_route(OLD.`路线ID`);
    CALL recompute_summary_for_route(OLD.`路线ID`);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table goods_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_goods_total_after_delete`;
delimiter ;;
CREATE TRIGGER `trg_goods_total_after_delete` AFTER DELETE ON `goods_total` FOR EACH ROW BEGIN
    UPDATE routes r
    SET r.货值 = (
        SELECT COALESCE(SUM(gt.货值), 0) + COALESCE(
            (SELECT SUM(gd.总价) FROM goods_details gd WHERE gd.路线ID = OLD.路线ID), 0
        )
        FROM goods_total gt
        WHERE gt.路线ID = OLD.路线ID
    )
    WHERE r.路线ID = OLD.路线ID;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table routes
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_routes_bi`;
delimiter ;;
CREATE TRIGGER `trg_routes_bi` BEFORE INSERT ON `routes` FOR EACH ROW BEGIN
    -- ★ v3.0: 如果计费重量为null,自动设置为实际重量
    IF NEW.`计费重量(/kg)` IS NULL AND NEW.`实际重量(/kg)` IS NOT NULL THEN
        SET NEW.`计费重量(/kg)` = NEW.`实际重量(/kg)`;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table routes
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_routes_bu`;
delimiter ;;
CREATE TRIGGER `trg_routes_bu` BEFORE UPDATE ON `routes` FOR EACH ROW BEGIN
    -- ★ v3.0: 如果计费重量被设置为null,自动使用实际重量
    IF NEW.`计费重量(/kg)` IS NULL AND NEW.`实际重量(/kg)` IS NOT NULL THEN
        SET NEW.`计费重量(/kg)` = NEW.`实际重量(/kg)`;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table routes
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_routes_au`;
delimiter ;;
CREATE TRIGGER `trg_routes_au` AFTER UPDATE ON `routes` FOR EACH ROW BEGIN
    -- 如果货值发生变化,则触发该路线下所有代理的 summary 重新计算
    IF NEW.`货值` <> OLD.`货值` THEN
        CALL recompute_summary_for_route(NEW.`路线ID`);
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table summary
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_summary_before_insert`;
delimiter ;;
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
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table summary
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_summary_before_update`;
delimiter ;;
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
END
;;
delimiter ;

SET FOREIGN_KEY_CHECKS = 1;
