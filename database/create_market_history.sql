-- 汇率历史记录表（每日快照）
DROP TABLE IF EXISTS `forex_rate_history`;
CREATE TABLE `forex_rate_history` (
  `id`       INT AUTO_INCREMENT PRIMARY KEY,
  `币种`      VARCHAR(10) NOT NULL,
  `汇率`      DECIMAL(12, 6) NOT NULL COMMENT '1单位外币=?人民币',
  `参考日期`   DATE NOT NULL,
  UNIQUE KEY `uk_currency_date` (`币种`, `参考日期`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 上海原油期货价格历史（SC888主力合约，元/桶，用于燃油附加费参考）
DROP TABLE IF EXISTS `fuel_price_history`;
CREATE TABLE `fuel_price_history` (
  `id`       INT AUTO_INCREMENT PRIMARY KEY,
  `收盘价`    DECIMAL(10, 4) NOT NULL COMMENT '上期所SC888收盘价，元/桶',
  `交易日期`   DATE NOT NULL,
  UNIQUE KEY `uk_date` (`交易日期`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
