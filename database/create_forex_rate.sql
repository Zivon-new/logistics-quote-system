-- 汇率表：存储外币对人民币的汇率（1外币=?CNY）
-- 数据源：ExchangeRate-API (open.er-api.com)，每日 09:30 自动同步
-- 注意：若旧表列名不同，先 DROP 重建
DROP TABLE IF EXISTS `forex_rate`;
CREATE TABLE `forex_rate` (
  `id`       INT AUTO_INCREMENT PRIMARY KEY,
  `币种`      VARCHAR(10) NOT NULL,
  `汇率`      DECIMAL(12, 6) NOT NULL COMMENT '1单位外币=?人民币',
  `参考日期`   DATE NOT NULL,
  `更新时间`   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY `uk_currency` (`币种`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 初始数据（兜底值，首次同步前使用）
INSERT INTO `forex_rate` (`币种`, `汇率`, `参考日期`) VALUES
  ('USD', 7.2000, CURDATE()),
  ('EUR', 7.8000, CURDATE()),
  ('SGD', 5.3000, CURDATE()),
  ('JPY', 0.0480, CURDATE()),
  ('MYR', 1.6000, CURDATE())
ON DUPLICATE KEY UPDATE `汇率` = VALUES(`汇率`), `参考日期` = VALUES(`参考日期`);
