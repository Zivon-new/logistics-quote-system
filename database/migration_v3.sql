-- ============================================================
-- migration_v3.sql
-- 国际物流智能报价及推荐系统 — 数据库升级迁移脚本
-- 版本: v3.0
-- 日期: 2026-03-12
-- 说明: 支持智能推荐、港口地图、航线风险、AI企业背调等新模块
-- ============================================================
-- ⚠️  执行前请备份数据库：
--   mysqldump -u root -p price_test_v2 > price_test_v2_backup_before_v3.sql
-- ============================================================

USE `price_test_v2`;

SET FOREIGN_KEY_CHECKS = 0;
SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';


-- ============================================================
-- PART 1: 新建表
-- ============================================================

-- ------------------------------------------------------------
-- 1.1 代理商主表 agents
--     将 route_agents.代理商 从自由文本规范化为主表引用
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `agents` (
    `代理商ID`      INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    `代理商名称`    VARCHAR(100)    NOT NULL                COMMENT '公司全称（唯一索引）',
    `代理商简称`    VARCHAR(50)     DEFAULT NULL            COMMENT '常用缩写/简称',
    `国家地区`      VARCHAR(50)     DEFAULT NULL            COMMENT '代理商所在国家或地区',
    `主营路线`      VARCHAR(200)    DEFAULT NULL            COMMENT '逗号分隔，如"深圳-新加坡,上海-荷兰"',
    `主营运输方式`  VARCHAR(50)     DEFAULT NULL            COMMENT '海运/空运/铁路/多式联运',
    `合作状态`      ENUM('已合作','未合作','待确认')
                                    NOT NULL DEFAULT '已合作',
    `信用评分`      TINYINT UNSIGNED DEFAULT NULL           COMMENT '1-100，推荐引擎打分',
    `联系方式`      VARCHAR(200)    DEFAULT NULL,
    `备注`          TEXT            DEFAULT NULL,
    `创建时间`      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `更新时间`      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`代理商ID`),
    UNIQUE KEY `uk_agents_name` (`代理商名称`),
    KEY `idx_agents_status` (`合作状态`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='代理商主表，规范化自 route_agents.代理商';


-- ------------------------------------------------------------
-- 1.2 全球港口表 ports
--     基于 UN/LOCODE，存储主要港口的位置和风险信息
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `ports` (
    `港口ID`        INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    `UNLOCODE`      VARCHAR(10)     NOT NULL                COMMENT 'UN/LOCODE，如 CNSZX',
    `港口名称`      VARCHAR(100)    NOT NULL                COMMENT '中文名称',
    `港口英文名`    VARCHAR(100)    DEFAULT NULL,
    `国家代码`      CHAR(2)         NOT NULL                COMMENT 'ISO 3166-1 alpha-2',
    `国家名称`      VARCHAR(60)     NOT NULL,
    `城市`          VARCHAR(60)     DEFAULT NULL,
    `纬度`          DECIMAL(9,6)    DEFAULT NULL,
    `经度`          DECIMAL(9,6)    DEFAULT NULL,
    `港口类型`      ENUM('海港','空港','内陆港','铁路港','多式联运')
                                    NOT NULL DEFAULT '海港',
    `所属时区`      VARCHAR(50)     DEFAULT NULL            COMMENT '如 Asia/Shanghai',
    `平均清关天数`  DECIMAL(4,1)    DEFAULT NULL            COMMENT '历史平均清关天数',
    `LPI风险等级`   ENUM('低','中','高')
                                    DEFAULT '中'            COMMENT '基于LPI综合评估',
    `备注`          VARCHAR(500)    DEFAULT NULL,
    `更新时间`      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`港口ID`),
    UNIQUE KEY `uk_ports_unlocode` (`UNLOCODE`),
    KEY `idx_ports_country` (`国家代码`),
    KEY `idx_ports_type` (`港口类型`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='全球主要港口表，基于UN/LOCODE';


-- ------------------------------------------------------------
-- 1.3 世界银行物流绩效指数 country_lpi
--     数据来源：World Bank LPI 2023
--     https://lpi.worldbank.org/
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `country_lpi` (
    `lpiID`         INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    `国家代码`      CHAR(2)         NOT NULL                COMMENT 'ISO 3166-1 alpha-2',
    `国家名称`      VARCHAR(60)     NOT NULL,
    `国家中文名`    VARCHAR(60)     DEFAULT NULL,
    `数据年份`      YEAR            NOT NULL                COMMENT 'LPI调查年份',
    `LPI综合评分`   DECIMAL(4,2)    DEFAULT NULL            COMMENT '1-5分',
    `通关效率`      DECIMAL(4,2)    DEFAULT NULL            COMMENT 'Customs（海关效率）',
    `基础设施`      DECIMAL(4,2)    DEFAULT NULL            COMMENT 'Infrastructure',
    `国际运输`      DECIMAL(4,2)    DEFAULT NULL            COMMENT 'International Shipments',
    `物流能力`      DECIMAL(4,2)    DEFAULT NULL            COMMENT 'Logistics Competence',
    `货物追踪`      DECIMAL(4,2)    DEFAULT NULL            COMMENT 'Tracking & Tracing',
    `时效性`        DECIMAL(4,2)    DEFAULT NULL            COMMENT 'Timeliness',
    `全球排名`      SMALLINT UNSIGNED DEFAULT NULL,
    `风险等级`      ENUM('低','中低','中','中高','高')
                                    GENERATED ALWAYS AS (
                                        CASE
                                            WHEN `LPI综合评分` >= 4.0 THEN '低'
                                            WHEN `LPI综合评分` >= 3.5 THEN '中低'
                                            WHEN `LPI综合评分` >= 3.0 THEN '中'
                                            WHEN `LPI综合评分` >= 2.5 THEN '中高'
                                            ELSE '高'
                                        END
                                    ) STORED                COMMENT '基于LPI综合评分自动生成',
    `创建时间`      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`lpiID`),
    UNIQUE KEY `uk_lpi_country_year` (`国家代码`, `数据年份`),
    KEY `idx_lpi_score` (`LPI综合评分`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='世界银行物流绩效指数（LPI），用于航线风险评估';


-- ------------------------------------------------------------
-- 1.4 AI企业背调历史 agent_check_history
--     存储对代理商进行LLM背调的历史记录和报告
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `agent_check_history` (
    `查调ID`        INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    `代理商ID`      INT UNSIGNED    DEFAULT NULL            COMMENT '关联 agents.代理商ID，可为NULL（查调未入库的公司）',
    `查询关键词`    VARCHAR(200)    NOT NULL                COMMENT '用户输入的公司名/关键词',
    `llm模型`       VARCHAR(50)     DEFAULT NULL            COMMENT '调用的LLM模型，如 glm-4.7',
    `报告摘要`      TEXT            DEFAULT NULL            COMMENT 'LLM生成的背调报告摘要（300字以内）',
    `完整报告`      MEDIUMTEXT      DEFAULT NULL            COMMENT 'LLM生成的完整报告JSON',
    `风险评级`      ENUM('低风险','中等风险','高风险','无法评估')
                                    DEFAULT '无法评估',
    `信息来源`      VARCHAR(500)    DEFAULT NULL            COMMENT '参考的公开信息来源URL列表',
    `token消耗`     INT UNSIGNED    DEFAULT NULL,
    `查调耗时秒`    DECIMAL(6,2)    DEFAULT NULL,
    `操作用户`      VARCHAR(50)     DEFAULT NULL,
    `创建时间`      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`查调ID`),
    KEY `idx_check_keyword` (`查询关键词`(50)),
    KEY `idx_check_agent` (`代理商ID`),
    KEY `idx_check_time` (`创建时间`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='AI企业背调历史记录';


-- ============================================================
-- PART 2: 修改现有表
-- ============================================================

-- ------------------------------------------------------------
-- 2.1 route_agents 添加 代理商ID 和 时效天数
-- ------------------------------------------------------------
ALTER TABLE `route_agents`
    ADD COLUMN `代理商ID`  INT UNSIGNED DEFAULT NULL
        COMMENT '关联 agents.代理商ID，规范化后填充'
        AFTER `代理商`,
    ADD COLUMN `时效天数`  SMALLINT UNSIGNED DEFAULT NULL
        COMMENT '从时效字段提取的数字天数，用于排序和推荐'
        AFTER `时效`;

-- 为新列建索引
ALTER TABLE `route_agents`
    ADD KEY `idx_ra_agent_id` (`代理商ID`),
    ADD KEY `idx_ra_timeliness` (`时效天数`);


-- ------------------------------------------------------------
-- 2.2 routes 添加 起始港口ID 和 目的港口ID
-- ------------------------------------------------------------
ALTER TABLE `routes`
    ADD COLUMN `起始港口ID`  INT UNSIGNED DEFAULT NULL
        COMMENT '关联 ports.港口ID'
        AFTER `目的地`,
    ADD COLUMN `目的港口ID`  INT UNSIGNED DEFAULT NULL
        COMMENT '关联 ports.港口ID'
        AFTER `起始港口ID`;

ALTER TABLE `routes`
    ADD KEY `idx_routes_origin_port` (`起始港口ID`),
    ADD KEY `idx_routes_dest_port` (`目的港口ID`);


-- ------------------------------------------------------------
-- 2.3 goods_details 添加 货物大类
-- ------------------------------------------------------------
ALTER TABLE `goods_details`
    ADD COLUMN `货物大类`  VARCHAR(50) DEFAULT NULL
        COMMENT '如: 电子产品/纺织品/化工品/机械设备/食品/其他'
        AFTER `货物名称`;


-- ============================================================
-- PART 3: 种子数据 — 全球主要港口
-- ============================================================

INSERT INTO `ports`
    (`UNLOCODE`, `港口名称`, `港口英文名`, `国家代码`, `国家名称`, `城市`,
     `纬度`, `经度`, `港口类型`, `所属时区`, `平均清关天数`, `LPI风险等级`)
VALUES
-- 中国大陆
('CNSZX', '深圳港',     'Shenzhen Port',        'CN', '中国', '深圳',   22.543096,  114.057865, '海港', 'Asia/Shanghai',  2.0, '低'),
('CNSHA', '上海港',     'Shanghai Port',         'CN', '中国', '上海',   31.231706,  121.472644, '海港', 'Asia/Shanghai',  2.5, '低'),
('CNGZU', '广州港',     'Guangzhou Port',        'CN', '中国', '广州',   23.129110,  113.264385, '海港', 'Asia/Shanghai',  2.5, '低'),
('CNNGB', '宁波舟山港', 'Ningbo-Zhoushan Port',  'CN', '中国', '宁波',   29.868336,  121.549792, '海港', 'Asia/Shanghai',  2.5, '低'),
('CNQIN', '青岛港',     'Qingdao Port',          'CN', '中国', '青岛',   36.067082,  120.382595, '海港', 'Asia/Shanghai',  2.5, '低'),
('CNPEK', '北京首都机场','Beijing Capital Airport','CN', '中国', '北京',   40.080111,  116.584556, '空港', 'Asia/Shanghai',  1.5, '低'),
('CNCAN', '广州白云机场','Guangzhou Baiyun Airport','CN','中国','广州',  23.392436,  113.299217, '空港', 'Asia/Shanghai',  1.5, '低'),
-- 香港/澳门
('HKHKG', '香港港',     'Hong Kong Port',        'HK', '香港', '香港',   22.302711,  114.177216, '海港', 'Asia/Hong_Kong', 1.5, '低'),
('MOHKG', '澳门',       'Macau',                 'MO', '澳门', '澳门',   22.198745,  113.543873, '多式联运', 'Asia/Macau',  2.0, '低'),
-- 东南亚
('SGSIN', '新加坡港',   'Singapore Port',        'SG', '新加坡', '新加坡', 1.290270, 103.851959, '海港', 'Asia/Singapore', 1.0, '低'),
('VNSGN', '胡志明市港', 'Ho Chi Minh Port',      'VN', '越南', '胡志明市', 10.762622, 106.660172, '海港', 'Asia/Ho_Chi_Minh',4.0,'中'),
('VNHAN', '河内内排机场','Hanoi Noi Bai Airport', 'VN', '越南', '河内',   21.218000,  105.804000, '空港', 'Asia/Ho_Chi_Minh',3.5,'中'),
('PHMNL', '马尼拉港',   'Manila Port',           'PH', '菲律宾', '马尼拉', 14.592944, 120.981590, '海港', 'Asia/Manila',    5.0, '中'),
('MYPEN', '槟城港',     'Penang Port',           'MY', '马来西亚','槟城', 5.414168,  100.329895, '海港', 'Asia/Kuala_Lumpur',3.0,'中低'),
-- 日本/韩国
('JPTYO', '东京港',     'Tokyo Port',            'JP', '日本', '东京',   35.689487,  139.691711, '海港', 'Asia/Tokyo',     2.0, '低'),
('JPOSA', '大阪港',     'Osaka Port',            'JP', '日本', '大阪',   34.693738,  135.502165, '海港', 'Asia/Tokyo',     2.0, '低'),
('KRPUS', '釜山港',     'Busan Port',            'KR', '韩国', '釜山',   35.179554,  129.075638, '海港', 'Asia/Seoul',     2.0, '低'),
-- 中东
('AEDXB', '迪拜港',     'Dubai Port (Jebel Ali)', 'AE', '阿联酋', '迪拜', 24.978325,  55.113888, '海港', 'Asia/Dubai',     3.0, '中低'),
('SAJTD', '吉达伊斯兰港','Jeddah Islamic Port',  'SA', '沙特', '吉达',   21.485811,  39.192505, '海港', 'Asia/Riyadh',    5.0, '中'),
-- 欧洲
('NLRTM', '鹿特丹港',   'Rotterdam Port',        'NL', '荷兰', '鹿特丹', 51.904823,   4.462456, '海港', 'Europe/Amsterdam',2.0,'低'),
('DEHAM', '汉堡港',     'Hamburg Port',          'DE', '德国', '汉堡',   53.550341,   9.993682, '海港', 'Europe/Berlin',  2.0, '低'),
('DEFRA', '法兰克福机场','Frankfurt Airport',     'DE', '德国', '法兰克福', 50.037933,  8.562152, '空港', 'Europe/Berlin',  2.0, '低'),
('GBFXT', '费利克斯托港','Felixstowe Port',       'GB', '英国', '费利克斯托', 51.963600, 1.351080, '海港', 'Europe/London',  2.5, '低'),
('GBLON', '伦敦希思罗机场','London Heathrow',     'GB', '英国', '伦敦',   51.477500,  -0.461389, '空港', 'Europe/London',  2.0, '低'),
('ESBCN', '巴塞罗那港', 'Barcelona Port',        'ES', '西班牙', '巴塞罗那', 41.380894, 2.122387, '海港', 'Europe/Madrid',  3.0, '低'),
('ESVLC', '瓦伦西亚港', 'Valencia Port',         'ES', '西班牙', '瓦伦西亚', 39.469907, -0.376288, '海港', 'Europe/Madrid', 3.0, '低'),
-- 北美
('USLAX', '洛杉矶港',   'Los Angeles Port',      'US', '美国', '洛杉矶', 33.754185, -118.216458, '海港', 'America/Los_Angeles', 3.0, '低'),
('USDAL', '达拉斯机场', 'Dallas/Fort Worth Airport','US','美国','达拉斯', 32.899809,  -97.040335, '空港', 'America/Chicago', 2.5,'低'),
('USMIA', '迈阿密机场', 'Miami International Airport','US','美国','迈阿密', 25.795865, -80.287046, '空港', 'America/New_York', 2.5,'低'),
('USSJO', '圣何塞机场', 'Norman Y. Mineta San Jose Airport','US','美国','圣何塞', 37.363947, -121.929024, '空港', 'America/Los_Angeles', 2.5,'低'),
-- 澳洲
('AUSYD', '悉尼港',     'Sydney Port',           'AU', '澳大利亚', '悉尼', -33.868820, 151.209290, '海港', 'Australia/Sydney', 3.5, '低'),
('AUMEL', '墨尔本港',   'Melbourne Port',        'AU', '澳大利亚', '墨尔本', -37.813630, 144.963058, '海港', 'Australia/Melbourne', 3.5, '低')
ON DUPLICATE KEY UPDATE
    `港口名称`      = VALUES(`港口名称`),
    `纬度`          = VALUES(`纬度`),
    `经度`          = VALUES(`经度`),
    `平均清关天数`  = VALUES(`平均清关天数`),
    `LPI风险等级`   = VALUES(`LPI风险等级`);


-- ============================================================
-- PART 4: 种子数据 — 世界银行 LPI 2023
--   来源: World Bank LPI 2023 (https://lpi.worldbank.org/)
--   评分范围 1-5，越高越好
-- ============================================================

INSERT INTO `country_lpi`
    (`国家代码`, `国家名称`, `国家中文名`, `数据年份`,
     `LPI综合评分`, `通关效率`, `基础设施`, `国际运输`, `物流能力`, `货物追踪`, `时效性`, `全球排名`)
VALUES
--  CN   China
('CN', 'China',        '中国',     2023, 3.68, 3.44, 3.80, 3.48, 3.66, 3.73, 3.95,  22),
--  SG   Singapore
('SG', 'Singapore',    '新加坡',   2023, 4.30, 4.20, 4.37, 4.00, 4.25, 4.36, 4.62,   1),
--  DE   Germany
('DE', 'Germany',      '德国',     2023, 4.20, 4.10, 4.32, 4.02, 4.22, 4.26, 4.39,   4),
--  NL   Netherlands
('NL', 'Netherlands',  '荷兰',     2023, 4.19, 4.07, 4.29, 3.91, 4.22, 4.27, 4.40,   5),
--  GB   United Kingdom
('GB', 'United Kingdom','英国',    2023, 3.95, 3.80, 4.03, 3.72, 3.96, 4.03, 4.19,  11),
--  JP   Japan
('JP', 'Japan',        '日本',     2023, 4.03, 3.80, 4.13, 3.75, 4.06, 4.12, 4.34,   7),
--  KR   South Korea
('KR', 'Korea, Rep.',  '韩国',     2023, 3.81, 3.62, 3.93, 3.61, 3.83, 3.87, 4.01,  17),
--  AE   UAE (Dubai)
('AE', 'United Arab Emirates','阿联酋', 2023, 4.06, 4.02, 4.07, 3.70, 3.99, 4.13, 4.43,   6),
--  SA   Saudi Arabia
('SA', 'Saudi Arabia', '沙特',     2023, 3.38, 3.28, 3.46, 3.23, 3.32, 3.42, 3.60,  38),
--  VN   Vietnam
('VN', 'Viet Nam',     '越南',     2023, 3.30, 3.00, 3.20, 3.26, 3.24, 3.41, 3.68,  43),
--  PH   Philippines
('PH', 'Philippines',  '菲律宾',   2023, 2.95, 2.76, 2.84, 2.92, 2.88, 3.06, 3.25,  68),
--  MY   Malaysia
('MY', 'Malaysia',     '马来西亚', 2023, 3.50, 3.24, 3.52, 3.42, 3.54, 3.57, 3.73,  31),
--  ES   Spain
('ES', 'Spain',        '西班牙',   2023, 3.83, 3.71, 3.91, 3.57, 3.83, 3.89, 4.05,  16),
--  AU   Australia
('AU', 'Australia',    '澳大利亚', 2023, 3.74, 3.62, 3.84, 3.49, 3.78, 3.78, 3.95,  19),
--  US   United States
('US', 'United States','美国',     2023, 3.87, 3.74, 4.01, 3.67, 3.88, 3.93, 4.03,  12),
--  HK   Hong Kong
('HK', 'Hong Kong SAR, China','香港', 2023, 4.06, 3.88, 4.09, 3.81, 4.05, 4.09, 4.44,   8)
ON DUPLICATE KEY UPDATE
    `LPI综合评分` = VALUES(`LPI综合评分`),
    `通关效率`    = VALUES(`通关效率`),
    `基础设施`    = VALUES(`基础设施`),
    `国际运输`    = VALUES(`国际运输`),
    `物流能力`    = VALUES(`物流能力`),
    `货物追踪`    = VALUES(`货物追踪`),
    `时效性`      = VALUES(`时效性`),
    `全球排名`    = VALUES(`全球排名`);


-- ============================================================
-- PART 5: 种子数据 — 补充汇率
-- ============================================================

INSERT INTO `forex_rate` (`货币代码`, `人民币汇率`, `更新时间`)
VALUES
    ('USD', 7.24, NOW()),
    ('EUR', 7.85, NOW()),
    ('GBP', 9.10, NOW()),
    ('JPY', 0.048, NOW()),
    ('HKD', 0.93, NOW()),
    ('AUD', 4.72, NOW()),
    ('SGD', 5.36, NOW()),
    ('AED', 1.97, NOW()),
    ('SAR', 1.93, NOW()),
    ('MYR', 1.66, NOW()),
    ('VND', 0.00029, NOW()),
    ('KRW', 0.0052, NOW()),
    ('PHP', 0.127, NOW())
ON DUPLICATE KEY UPDATE
    `人民币汇率` = VALUES(`人民币汇率`),
    `更新时间`   = VALUES(`更新时间`);


-- ============================================================
-- PART 6: 数据迁移
-- ============================================================

-- ------------------------------------------------------------
-- 6.1 从 route_agents.代理商 提取不重复的公司名，填入 agents 主表
--     只导入非空、非"未知"、长度合理（2-100字符）的代理商名称
-- ------------------------------------------------------------
INSERT IGNORE INTO `agents` (`代理商名称`, `合作状态`)
SELECT DISTINCT
    TRIM(`代理商`)     AS `代理商名称`,
    '已合作'           AS `合作状态`
FROM `route_agents`
WHERE `代理商` IS NOT NULL
  AND TRIM(`代理商`) != ''
  AND TRIM(`代理商`) NOT IN ('未知', 'unknown', '待确认', '?', '-')
  AND CHAR_LENGTH(TRIM(`代理商`)) BETWEEN 2 AND 100;


-- ------------------------------------------------------------
-- 6.2 将 route_agents.代理商ID 关联到 agents 主表
-- ------------------------------------------------------------
UPDATE `route_agents` ra
    INNER JOIN `agents` a ON a.`代理商名称` = TRIM(ra.`代理商`)
SET ra.`代理商ID` = a.`代理商ID`
WHERE ra.`代理商` IS NOT NULL;


-- ------------------------------------------------------------
-- 6.3 从 route_agents.时效 提取数字天数，写入 时效天数
--     支持的格式：
--       "15天"        → 15
--       "15-20天"     → 17  (取平均)
--       "10-15个工作日"→ 12 (取平均)
--       "约20天"      → 20
--       "3周"         → 21
-- ------------------------------------------------------------
UPDATE `route_agents`
SET `时效天数` = CASE
    -- "X-Y天" 或 "X-Y工作日" → 取均值
    WHEN `时效` REGEXP '[0-9]+-[0-9]+(天|工作日|days?)' THEN
        ROUND(
            (CAST(SUBSTRING_INDEX(`时效`, '-', 1) AS UNSIGNED) +
             CAST(REGEXP_SUBSTR(SUBSTRING_INDEX(`时效`, '-', -1), '[0-9]+') AS UNSIGNED)) / 2
        )
    -- "X周" → X*7
    WHEN `时效` REGEXP '[0-9]+周' THEN
        CAST(REGEXP_SUBSTR(`时效`, '[0-9]+') AS UNSIGNED) * 7
    -- "约X天"、"X天"、纯数字 → X
    WHEN `时效` REGEXP '[0-9]+(天|days?)' THEN
        CAST(REGEXP_SUBSTR(`时效`, '[0-9]+') AS UNSIGNED)
    -- 其他情况保持NULL
    ELSE NULL
END
WHERE `时效` IS NOT NULL
  AND `时效天数` IS NULL;


-- ============================================================
-- PART 7: 更新 agents 主表的 主营路线（辅助统计，非关键）
-- ============================================================

-- 更新主营运输方式（取该代理商出现最多的运输方式）
UPDATE `agents` a
INNER JOIN (
    SELECT
        `代理商ID`,
        `运输方式`,
        COUNT(*) AS cnt,
        ROW_NUMBER() OVER (PARTITION BY `代理商ID` ORDER BY COUNT(*) DESC) AS rn
    FROM `route_agents`
    WHERE `代理商ID` IS NOT NULL
      AND `运输方式` IS NOT NULL
      AND `运输方式` != ''
    GROUP BY `代理商ID`, `运输方式`
) top_mode ON top_mode.`代理商ID` = a.`代理商ID` AND top_mode.rn = 1
SET a.`主营运输方式` = top_mode.`运输方式`;


-- ============================================================
-- PART 8: 验证查询（执行后检查结果是否符合预期）
-- ============================================================

-- 检查各表记录数
SELECT '代理商主表' AS 表名, COUNT(*) AS 记录数 FROM `agents`
UNION ALL
SELECT '全球港口表', COUNT(*) FROM `ports`
UNION ALL
SELECT '国家LPI表', COUNT(*) FROM `country_lpi`
UNION ALL
SELECT '背调历史表', COUNT(*) FROM `agent_check_history`;

-- 检查代理商ID关联率
SELECT
    COUNT(*) AS route_agents总数,
    SUM(CASE WHEN `代理商ID` IS NOT NULL THEN 1 ELSE 0 END) AS 已关联代理商ID,
    ROUND(SUM(CASE WHEN `代理商ID` IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) * 100, 1) AS 关联率百分比
FROM `route_agents`;

-- 检查时效天数提取率
SELECT
    COUNT(*) AS 有时效文本的记录,
    SUM(CASE WHEN `时效天数` IS NOT NULL THEN 1 ELSE 0 END) AS 已提取天数,
    ROUND(SUM(CASE WHEN `时效天数` IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) * 100, 1) AS 提取率
FROM `route_agents`
WHERE `时效` IS NOT NULL AND `时效` != '';

-- 列出新增代理商（前20个）
SELECT `代理商ID`, `代理商名称`, `主营运输方式`, `合作状态` FROM `agents` LIMIT 20;

-- 按运输方式统计代理商数量
SELECT `主营运输方式`, COUNT(*) AS 代理商数量
FROM `agents`
GROUP BY `主营运输方式`
ORDER BY 代理商数量 DESC;


SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- 迁移完成
-- 如需回滚，执行：
--   DROP TABLE IF EXISTS agents, ports, country_lpi, agent_check_history;
--   ALTER TABLE route_agents DROP COLUMN 代理商ID, DROP COLUMN 时效天数;
--   ALTER TABLE routes DROP COLUMN 起始港口ID, DROP COLUMN 目的港口ID;
--   ALTER TABLE goods_details DROP COLUMN 货物大类;
-- ============================================================
