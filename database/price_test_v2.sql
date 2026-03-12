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

 Date: 12/03/2026 14:43:18
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

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
  `币种` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'RMB',
  `原币金额` decimal(18, 2) NULL DEFAULT 0.00,
  `人民币金额` decimal(18, 2) NULL DEFAULT 0.00,
  `备注` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `创建时间` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`费用ID`) USING BTREE,
  INDEX `fk_fee_items_route_agents`(`代理路线ID` ASC) USING BTREE,
  CONSTRAINT `fk_fee_items_route_agents` FOREIGN KEY (`代理路线ID`) REFERENCES `route_agents` (`代理路线ID`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 136 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of fee_items
-- ----------------------------
INSERT INTO `fee_items` VALUES (1, 1, '海运费', 18.00, '/kg', 1740.000, 'RMB', 31320.00, 31320.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (2, 1, '附加费', 5.00, '/kg', 1740.000, 'RMB', 8700.00, 8700.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (3, 2, '运费', 22.00, '/kg', 1740.000, 'RMB', 38280.00, 38280.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (4, 3, '运费', 17.00, '/kg', 1740.000, 'RMB', 29580.00, 29580.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (5, 4, '海运费', 500.00, '/cbm', 5.460, 'RMB', 2730.00, 2730.00, '如需拆箱：500元*2=1000', '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (6, 5, '海运费', 380.00, '/cbm', 5.460, 'RMB', 2074.80, 2074.80, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (7, 6, '海运费', 14.50, '/kg', 910.000, 'RMB', 13195.00, 13195.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (8, 7, '运费', 8.00, '/kg', 930.000, 'RMB', 7440.00, 7440.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (9, 7, '卸货费', 300.00, '/人/小时', 4.000, 'RMB', 1200.00, 1200.00, '按照2小时2人计算', '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (10, 7, '拆箱费', 300.00, '/个', 2.000, 'RMB', 600.00, 600.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (11, 8, '集运费', 3.00, '/kg', 930.000, 'RMB', 2790.00, 2790.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (12, 8, '派送费', 800.00, '/次', 1.000, 'RMB', 800.00, 800.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (13, 9, '运费', 7.00, '/kg', 0.000, 'RMB', 0.00, 0.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (14, 9, '派送费', 500.00, '/票', 1.000, 'RMB', 500.00, 500.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (15, 10, '运费', 11.00, '/kg', 0.000, 'RMB', 0.00, 0.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (16, 10, '超长费', 300.00, '/件', 1.000, 'RMB', 300.00, 300.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (17, 10, '超重费', 300.00, '/件', 1.000, 'RMB', 300.00, 300.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (18, 10, '尾板费', 500.00, '/票', 1.000, 'RMB', 500.00, 500.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (19, 11, '运费', 1.50, '/kg', 0.000, 'RMB', 0.00, 0.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (20, 12, '包装费', 60.00, '/个', 2.000, 'USD', 120.00, 120.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (21, 13, '空运费', 25.00, '/kg', 100.000, 'RMB', 2500.00, 2500.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (22, 13, '操作费', 0.30, '/kg', 100.000, 'SGD', 30.00, 168.00, 'MIN SGD35', '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (23, 15, '运费', 45.00, '/kg', 30.000, 'RMB', 1350.00, 1350.00, '低于30KG', '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (24, 16, '运费', 68.00, '/kg', 100.000, 'RMB', 6800.00, 6800.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (25, 17, '包装费', 60.00, '/个', 1.000, 'USD', 60.00, 60.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (26, 18, '空运费', 27.00, '/kg', 100.000, 'RMB', 2700.00, 2700.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (27, 18, '操作费', 0.30, '/kg', 100.000, 'SGD', 30.00, 168.00, 'MIN SGD35', '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (28, 19, '空运费', 26.00, '/kg', 45.000, 'RMB', 1170.00, 1170.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (29, 19, '运费', 0.30, '/kg', 45.000, 'USD', 13.50, 13.50, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (30, 19, 'SIRIM费', 180.00, '/个', 1.000, 'USD', 180.00, 180.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (31, 20, '运费', 44.00, '/kg', 30.000, 'RMB', 1320.00, 1320.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (32, 21, '运费', 30.00, '/kg', 30.000, 'RMB', 900.00, 900.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (33, 22, '运费', 48.00, '/kg', 150.000, 'RMB', 7200.00, 7200.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (34, 23, '运费', 12.97, '/kg', 3000.000, 'RMB', 38910.00, 38910.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (35, 23, '派送费', 5.70, '/kg', 3000.000, 'RMB', 17100.00, 17100.00, 'MIN 3360 RMB', '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (36, 23, '卸货费', 70.00, '/台', 100.000, 'RMB', 7000.00, 7000.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (37, 23, '仓储费', 1.50, '/天/kg', 15000.000, 'RMB', 22500.00, 22500.00, '免3天', '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (38, 24, '舱单费', 100.00, '/票', 1.000, 'RMB', 100.00, 100.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (39, 24, '卸货费', 0.55, '/kg', 3000.000, 'RMB', 1650.00, 1650.00, '或者 CNY120/板', '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (40, 24, '通关费', 12800.00, '/entry', 1.000, 'JPY', 12800.00, 12800.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (41, 24, '通关手续费', 11000.00, '/entry', 1.000, 'JPY', 11000.00, 11000.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (42, 24, 'THC费', 48.00, '/kg', 3000.000, 'JPY', 144000.00, 144000.00, 'min JPY6500', '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (43, 24, '操作费', 15000.00, '/hawb', 1.000, 'JPY', 15000.00, 15000.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (44, 24, 'handlift费', 6000.00, '/台', 2.000, 'JPY', 12000.00, 12000.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (45, 24, '上楼费', 35000.00, '/人', 4.000, 'JPY', 140000.00, 140000.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (46, 25, '运费', 55.00, '/kg', 120.000, 'RMB', 6600.00, 6600.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (47, 26, '快递费', 64.00, '/kg', 120.000, 'RMB', 7680.00, 7680.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (48, 27, '运费', 2.50, '/kg', 17000.000, 'RMB', 42500.00, 42500.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (49, 27, '派送费', 150.00, '/票', 1.000, 'RMB', 150.00, 150.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (50, 28, '运费', 1500.00, '/票', 1.000, 'RMB', 1500.00, 1500.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (51, 28, '运费', 4.50, '/kg', 17000.000, 'RMB', 76500.00, 76500.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (52, 30, '运费', 3.00, '/kg', 27000.000, 'RMB', 81000.00, 81000.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (53, 30, '派送费', 150.00, '/票', 1.000, 'RMB', 150.00, 150.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (54, 31, '运费', 4.50, '/kg', 27000.000, 'RMB', 121500.00, 121500.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (55, 31, '资料费', 1500.00, '/票', 1.000, 'RMB', 1500.00, 1500.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (56, 14, '运费', 38.00, '/kg', 100.000, 'CNY', 3800.00, 3800.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (57, 33, '运费', 84.00, '/kg', 45.000, 'CNY', 3780.00, 3780.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (58, 24, '运费', 17.00, '/kg', 3000.000, 'RMB', 51000.00, 51000.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_items` VALUES (133, 144, '运费', 10.00, '/kg', 240.000, 'RMB', 2400.00, 2400.00, '666', '2026-03-11 11:00:07');
INSERT INTO `fee_items` VALUES (134, 145, '空运费', 40.00, '/kg', 50.000, 'RMB', 2000.00, 2000.00, '666', '2026-03-11 14:57:01');
INSERT INTO `fee_items` VALUES (135, 146, '空运费', 40.00, '/kg', 60.000, 'RMB', 2400.00, 2400.00, '777', '2026-03-11 17:43:33');

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
) ENGINE = InnoDB AUTO_INCREMENT = 173 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of fee_total
-- ----------------------------
INSERT INTO `fee_total` VALUES (1, 7, '派送费', 500.00, 'RMB', 500.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (2, 7, '扔垃圾费', 600.00, 'RMB', 600.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (3, 8, '卸货上楼并拆清费用费', 1200.00, 'RMB', 1200.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (4, 12, '提货费', 300.00, 'USD', 300.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (5, 12, '上楼费', 180.00, 'USD', 180.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (6, 12, 'UPS快递费', 450.00, 'USD', 450.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (7, 12, '操作费', 100.00, 'SGD', 560.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (8, 12, '清关费', 100.00, 'SGD', 560.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (9, 12, '出入库费', 45.00, 'SGD', 252.00, '一进一出分开收费', '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (10, 12, '派送费', 180.00, 'SGD', 1008.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (11, 12, '上楼费', 180.00, 'SGD', 1008.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (12, 12, '手续费', 65.00, 'SGD', 364.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (13, 13, '验电费', 500.00, 'RMB', 500.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (14, 13, '操作费', 200.00, 'RMB', 200.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (15, 13, '报关费', 300.00, 'RMB', 300.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (16, 13, '申报税费', 200.00, 'RMB', 200.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (17, 13, '报关费', 100.00, 'SGD', 560.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (18, 13, '卡车费', 180.00, 'SGD', 1008.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (19, 13, '人工费', 180.00, 'SGD', 1008.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (20, 13, '拆包装和回收垃圾费', 200.00, 'SGD', 1120.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (21, 13, '代理税金操作费', 65.00, 'SGD', 364.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (22, 15, '预约费', 500.00, 'RMB', 500.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (23, 15, '卸货上楼费', 500.00, 'RMB', 500.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (24, 16, '操作费', 200.00, 'RMB', 200.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (25, 16, '卸货费', 800.00, 'EUR', 800.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (26, 17, '提货费', 300.00, 'USD', 300.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (27, 17, '上楼费', 180.00, 'USD', 180.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (28, 17, 'UPS快递费', 350.00, 'USD', 350.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (29, 17, '调单费', 95.00, 'EUR', 95.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (30, 17, '清关费', 115.00, 'EUR', 115.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (31, 17, '操作费', 125.00, 'EUR', 125.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (32, 17, '贸易代理费', 380.00, 'EUR', 380.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (33, 17, '派送费', 280.00, 'EUR', 280.00, '预估的，拼车，不含卸货上楼', '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (34, 18, '操作费', 150.00, 'RMB', 150.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (35, 18, '报关费', 300.00, 'RMB', 300.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (36, 18, '报关费', 100.00, 'SGD', 560.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (37, 18, '卡车费', 200.00, 'SGD', 1120.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (38, 18, '人工费', 200.00, 'SGD', 1120.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (39, 18, '拆包装和回收垃圾费', 250.00, 'SGD', 1400.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (40, 19, '操作费', 150.00, 'RMB', 150.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (41, 19, '报关费', 300.00, 'RMB', 300.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (42, 19, '申报税费', 200.00, 'RMB', 200.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (43, 19, '报关费', 35.00, 'USD', 35.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (44, 19, '文件费', 35.00, 'USD', 35.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (45, 19, '贸易代理费', 180.00, 'USD', 180.00, 'IF NEED', '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (46, 19, '送货费', 150.00, 'USD', 150.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (47, 19, '卸货上楼费', 150.00, 'USD', 150.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (48, 19, '回收垃圾费', 80.00, 'USD', 80.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (49, 20, '操作费', 200.00, 'RMB', 200.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (50, 20, '派送费', 450.00, 'MYR', 450.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (51, 22, '操作费', 2500.00, 'RMB', 2500.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (52, 22, '如入朗华仓加收费', 1500.00, 'RMB', 1500.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (53, 22, '操作费', 200.00, 'RMB', 200.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (54, 22, '卸货上楼&回收垃圾费', 450.00, 'USD', 450.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (55, 23, '深圳香港费', 5500.00, 'RMB', 5500.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (56, 23, '出口清关杂费', 1775.00, 'RMB', 1775.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (57, 23, '目的港清关杂费', 2400.00, 'RMB', 2400.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (58, 23, '派送费', 2400.00, 'RMB', 2400.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (59, 23, '杂费', 2400.00, 'RMB', 2400.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (60, 24, '报关费', 300.00, 'RMB', 300.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (61, 24, '清关费', 300.00, 'RMB', 300.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (62, 24, '申报税费', 200.00, 'RMB', 200.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (63, 24, '香港本地杂费', 1000.00, 'RMB', 1000.00, '香港入仓费，停车费和隧道费等香港本地杂费实报实销 预估1000 左右', '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (64, 24, '验电费', 500.00, 'RMB', 500.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (65, 24, '提派费', 399800.00, 'JPY', 399800.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (66, 25, '派送费', 800.00, 'RMB', 800.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (67, 29, '国内报关费', 400.00, 'RMB', 400.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (68, 29, '送货费', 500.00, 'RMB', 500.00, '200-500元', '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (69, 29, '国外清关费', 200.00, 'USD', 200.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (70, 32, '国内报关费', 400.00, 'RMB', 400.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (71, 32, '送货费', 500.00, 'RMB', 500.00, '200-500元', '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (72, 32, '国外清关费', 200.00, 'USD', 200.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (73, 29, '柜费', 24000.00, 'RMB', 24000.00, '40尺柜*2 ：12000RMB*2', '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (74, 11, '交会展费', 1700.00, 'RMB', 1700.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (75, 11, '拆箱丢垃圾费', 1000.00, 'RMB', 1000.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (76, 14, '报关+过港费', 4500.00, 'CNY', 4500.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (77, 33, '操作费', 200.00, 'CNY', 200.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (78, 33, '报关费', 300.00, 'CNY', 300.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (79, 33, '验电费', 500.00, 'CNY', 500.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (80, 33, '报关费', 150.00, 'USD', 150.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (81, 33, '航站费', 280.00, 'USD', 280.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (82, 33, '贸易代理费', 200.00, 'USD', 200.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (83, 33, '操作费', 45.00, 'USD', 45.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (84, 33, '送货费', 385.00, 'USD', 385.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (85, 33, '人工费', 200.00, 'USD', 200.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (86, 33, '仓储费', 100.00, 'USD', 100.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (87, 33, '待时费', 150.00, 'USD', 150.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (88, 24, '贸易代理费', 35000.00, 'JPY', 35000.00, '货值*3.5%，min JPY35000（如需）', '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (89, 27, '提货费', 22110.00, 'RMB', 22110.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (90, 28, '提货费', 22110.00, 'RMB', 22110.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (91, 29, '提货费', 22110.00, 'RMB', 22110.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (92, 29, '柜费', 24000.00, 'RMB', 24000.00, '40尺柜*2 ：12000RMB*2', '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (93, 30, '提货费', 6000.00, 'RMB', 6000.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (94, 31, '提货费', 6000.00, 'RMB', 6000.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (95, 32, '提货费', 6000.00, 'RMB', 6000.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `fee_total` VALUES (170, 144, '操作费', 200.00, 'RMB', 200.00, '777', '2026-03-11 11:00:07');
INSERT INTO `fee_total` VALUES (171, 145, '操作费', 200.00, 'USD', 200.00, '777', '2026-03-11 14:57:01');
INSERT INTO `fee_total` VALUES (172, 146, '操作费', 200.00, 'USD', 200.00, '888', '2026-03-11 17:43:33');

-- ----------------------------
-- Table structure for forex_rate
-- ----------------------------
DROP TABLE IF EXISTS `forex_rate`;
CREATE TABLE `forex_rate`  (
  `币种` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `汇率` decimal(18, 8) NOT NULL,
  `更新时间` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`币种`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of forex_rate
-- ----------------------------
INSERT INTO `forex_rate` VALUES ('SGD', 5.60000000, '2026-02-24 17:18:44');

-- ----------------------------
-- Table structure for forex_rate_history
-- ----------------------------
DROP TABLE IF EXISTS `forex_rate_history`;
CREATE TABLE `forex_rate_history`  (
  `汇率历史ID` int NOT NULL AUTO_INCREMENT,
  `币种` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `汇率` decimal(18, 8) NOT NULL,
  `生效日期` date NOT NULL,
  `失效日期` date NULL DEFAULT NULL,
  `创建时间` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`汇率历史ID`) USING BTREE,
  INDEX `idx_currency_date`(`币种` ASC, `生效日期` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of forex_rate_history
-- ----------------------------

-- ----------------------------
-- Table structure for goods_details
-- ----------------------------
DROP TABLE IF EXISTS `goods_details`;
CREATE TABLE `goods_details`  (
  `货物ID` int NOT NULL AUTO_INCREMENT,
  `路线ID` int NOT NULL,
  `货物名称` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
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
) ENGINE = InnoDB AUTO_INCREMENT = 86 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of goods_details
-- ----------------------------
INSERT INTO `goods_details` VALUES (1, 7, 'CE88-D8CQ板卡', 0, '耗材', 10.000, 1200.0000, 'RMB', 0.500, 5.000, 12000.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (2, 8, 'Nokia 7750-SR-1（每台2块100G接口卡）', 1, '网络设备', 2.000, 132631.0000, 'RMB', 10.000, 20.000, 265262.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (3, 8, 'OTNS8600-DCI8', 1, '网络设备', 4.000, 2500.0000, 'RMB', 15.000, 60.000, 10000.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (4, 8, 'OTMT2光转换单元', 1, '网络设备', 8.000, 37000.0000, 'RMB', 1.500, 12.000, 296000.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (5, 9, '100G单模模块 QSFP28-100G-LR4(1310nm,10km,LC)', 1, '耗材', 21.000, 950.0000, 'RMB', 0.100, 2.100, 19950.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (6, 9, '100G多模模块 QSFP28-100G-SR4(850nm,0.1km,MPO)', 1, '耗材', 38.000, 168.0000, 'RMB', 0.100, 3.800, 6384.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (7, 9, 'MPO（100g多模） 10m', 1, '耗材', 40.000, 80.7000, 'RMB', 0.100, 4.000, 3228.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (8, 9, '光纤跳线 单模（LC-LC）10m', 1, '耗材', 42.000, 10.1500, 'RMB', 0.100, 4.200, 426.30, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (9, 9, 'AOC（25g）5m', 1, '耗材', 66.000, 117.0000, 'RMB', 0.100, 6.600, 7722.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (10, 9, '标签纸A4', 1, '耗材', 2.000, 20.0000, 'RMB', 0.100, 0.200, 40.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (11, 9, '理线架', 1, '耗材', 4.000, 25.0000, 'RMB', 0.100, 0.400, 100.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (12, 9, '魔术贴', 1, '耗材', 1.000, 40.0000, 'RMB', 0.100, 0.100, 40.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (13, 9, '扎带', 1, '耗材', 1.000, 38.0000, 'RMB', 0.100, 0.100, 38.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (14, 10, 'Nokia 7750-SR-1（每台2块100G接口卡）', 1, '网络设备', 2.000, 132631.0000, 'RMB', 10.000, 20.000, 265262.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (15, 10, 'MPO（100g多模） 15m', 0, '耗材', 32.000, 33.6500, 'RMB', 0.100, 3.200, 1076.80, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (16, 11, 'P616 光转换单元', 1, '网络设备', 6.000, 50000.0000, 'RMB', 1.500, 9.000, 300000.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (17, 11, 'Nokia 7750-SR-1（每台2块100G接口卡）', 1, '网络设备', 2.000, 132631.0000, 'RMB', 10.000, 20.000, 265262.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (18, 11, '100G单模模块 QSFP28-100G-LR4(1310nm,10km,LC)', 1, '耗材', 82.000, 950.0000, 'RMB', 0.100, 8.200, 77900.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (19, 11, 'MPO（100g多模） 10m', 1, '耗材', 30.000, 80.7000, 'RMB', 0.100, 3.000, 2421.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (20, 11, '单模（LC-LC）10m', 1, '耗材', 49.000, 10.1500, 'RMB', 0.100, 4.900, 497.35, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (21, 11, 'AOC（25g）5m', 1, '耗材', 66.000, 117.0000, 'RMB', 0.100, 6.600, 7722.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (22, 11, '标签纸A4', 1, '耗材', 2.000, 20.0000, 'RMB', 0.100, 0.200, 40.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (23, 11, '理线架', 1, '耗材', 10.000, 25.0000, 'RMB', 0.100, 1.000, 250.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (24, 11, '魔术贴', 1, '耗材', 5.000, 40.0000, 'RMB', 0.100, 0.500, 200.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (25, 11, '扎带', 1, '耗材', 5.000, 38.0000, 'RMB', 0.100, 0.500, 190.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (26, 11, '网线5m', 1, '耗材', 15.000, 19.0000, 'RMB', 0.100, 1.500, 285.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (27, 11, 'C13-C14电源线', 0, '耗材', 24.000, 25.0000, 'RMB', 0.100, 2.400, 600.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (28, 11, 'CE6865E', 0, '交换机', 2.000, 11248.0000, 'RMB', 8.000, 16.000, 22496.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (29, 12, '5120-48Y', 0, '交换机', 1.000, 11906.0000, 'RMB', 8.000, 8.000, 11906.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_details` VALUES (83, 110, '交换机', 1, '网络设备', 2.000, 50000.0000, 'RMB', 120.000, 240.000, 100000.00, '111', '2026-03-11 11:00:07');
INSERT INTO `goods_details` VALUES (84, 107, '服务器设备', 1, '网络设备', 1.000, 10000.0000, 'RMB', 40.000, 40.000, 10000.00, '000', '2026-03-11 14:57:01');
INSERT INTO `goods_details` VALUES (85, 109, '服务器', 1, '网络设备', 1.000, 10000.0000, 'RMB', 40.000, 40.000, 10000.00, '111', '2026-03-11 17:43:33');

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
  `总体积(/cbm)` decimal(18, 3) NULL DEFAULT 0.000 COMMENT '整单总体积,单位:立方米',
  `备注` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `创建时间` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`整单货物ID`) USING BTREE,
  INDEX `fk_goods_total_routes`(`路线ID` ASC) USING BTREE,
  CONSTRAINT `fk_goods_total_routes` FOREIGN KEY (`路线ID`) REFERENCES `routes` (`路线ID`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 46 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of goods_total
-- ----------------------------
INSERT INTO `goods_total` VALUES (1, 1, '碱性电池', 1740.00, 0.00, 0.000, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_total` VALUES (2, 2, '2件展示柜', 910.00, 100000.00, 5.460, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_total` VALUES (3, 3, '2件展示柜', 910.00, 100000.00, 5.460, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_total` VALUES (4, 4, '2件展示柜', 910.00, 0.00, 2.730, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_total` VALUES (5, 4, '粮食标本', 5.00, 0.00, 0.000, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_total` VALUES (6, 4, '电子屏', 10.00, 0.00, 0.002, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_total` VALUES (7, 4, '酿酒陶坛', 5.00, 0.00, 0.002, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_total` VALUES (8, 16, '4台Dell PowerEdge R7625', 150.00, 0.00, 0.000, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_total` VALUES (9, 19, '宣传册&伴手礼', 120.00, 0.00, 0.000, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_total` VALUES (10, 22, '长雨伞和短雨伞', 0.00, 0.00, 0.000, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_total` VALUES (11, 23, '风扇', 0.00, 0.00, 0.000, NULL, '2026-02-25 18:09:23');
INSERT INTO `goods_total` VALUES (43, 110, '交换机', 240.00, 100000.00, 5.000, '2台', '2026-03-11 11:00:07');
INSERT INTO `goods_total` VALUES (44, 107, '服务器', 40.00, 10000.00, 5.000, '111', '2026-03-11 14:57:01');
INSERT INTO `goods_total` VALUES (45, 109, '服务器设备', 40.00, 10000.00, 5.000, '222', '2026-03-11 17:43:34');

-- ----------------------------
-- Table structure for route_agents
-- ----------------------------
DROP TABLE IF EXISTS `route_agents`;
CREATE TABLE `route_agents`  (
  `代理路线ID` int NOT NULL AUTO_INCREMENT,
  `路线ID` int NOT NULL,
  `代理商` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `运输方式` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `贸易类型` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `代理备注` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `时效` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `时效备注` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `不含` varchar(511) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `是否赔付` tinyint(1) NULL DEFAULT 0 COMMENT '0=否，1=是',
  `赔付内容` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `创建时间` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`代理路线ID`) USING BTREE,
  INDEX `fk_route_agents_routes`(`路线ID` ASC) USING BTREE,
  CONSTRAINT `fk_route_agents_routes` FOREIGN KEY (`路线ID`) REFERENCES `routes` (`路线ID`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 147 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of route_agents
-- ----------------------------
INSERT INTO `route_agents` VALUES (1, 1, '融迅', '海运', '专线', NULL, '55天', '约50-55天左右，受天气原因影响较大，有晚开船、晚到港的情况，如遇托班/海关查验时间顺延', '国内提货费，保险费，二次包装费，存储费、送货时的卡车等待费、停车费等，如产生其他费用实报实销', 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (2, 1, '银顺达', '海运', '专线', '仅合作过快递，未合作过专线', '45天', '约45天左右，受天气原因影响较大，有晚开船、晚到港的情况，如遇托班/海关查验时间顺延', '国内提货费，保险费，二次包装费，存储费、送货时的卡车等待费、卸货上楼费、停车费等，如产生其他费用实报实销', 1, '电池专线赔偿标准：在运输过程中如货物丢失赔偿RMB40/kg，不退运费，尾程提取后丢失按照快递公司官方赔偿标准进行赔偿,最高不超过100美金/票', '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (3, 1, '欧洲专线集团', '快递', '专线', '展会新加代理，未合作', '55天', '约50-55天左右，受天气原因影响较大，有晚开船、晚到港的情况，如遇托班/海关查验时间顺延', '国内提货费，保险费，二次包装费，存储费、送货时的卡车等待费、卸货上楼费、停车费等，如产生其他费用实报实销', 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (4, 2, '越海速达', '海运', '双清', NULL, '15天', '时效：运输时间：12-15个工作日左右', '卸货拆箱等', 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (5, 2, '骐盛', '海运', '双清', NULL, NULL, '运输时间：近期船期乱，时效不稳定不做保证', '卸货拆箱等', 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (6, 3, '拓宇', '海运', '双清', NULL, '50天', '开船后时效50天左右到', NULL, 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (7, 4, '一诺物流', NULL, NULL, '新代理，未合作', '3天', '约2-3天，海关查验顺延', '保险费，查验费，待时费，国内转运费（天津-珠海），包装费', 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (8, 4, '雄展货运', NULL, NULL, '未合作，新代理', '2天', '约2天，海关查验顺延', '保险费，查验费，待时费，国内转运费（天津-珠海），包装费', 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (9, 5, '澳凯', '海运', '专线', '海运专线-新代理未合作', '30天', '展会货物建议尽早出运，以免遇到晚开船/查验等导致延误；开船后25-30天左右签收，受天气原因影响较大，有晚开船、晚到港的情况，如遇托班/海关查验时间顺延', '国内提货费，保险费，包装费，存储费、送货时的卡车等待费、停车费等，如产生其他费用实报实销', 1, '货物丢件 赔偿20/kg 不退运费', '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (10, 5, '蓝鹰', '海运', '专线', '海运专线-新代理未合作', '35天', '展会货物建议尽早出运，以免遇到晚开船/查验等导致延误；开船后约25-35天左右到，海运受天气原因影响较大，有晚开船、晚到港的情况，如遇托班/海关查验时间顺延', '国内提货费，保险费，包装费，存储费、送货时的卡车等待费、停车费等，如产生其他费用实报实销', 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (11, 6, '海阳中港', '海运', NULL, NULL, '4天', '展会货物建议尽早出运，以免遇到晚开船/查验等导致延误；约3-4个工作日过港（不含派送时间），如遇海关查验时间顺延，参考之前货物过港遇到查验退运，约2周左右重新发出', '香港杂费实报实销，国内提货费，保险费，包装费，存储费、送货时的卡车等待费、停车费等，如产生其他费用实报实销', 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (12, 7, '融迅', '快递', '快递', '快递+贸代方案', '12天', '提货+包装需要2-3天，快递4-6天， 清关+送货2-3天，全程：8-12天，海关查验顺延', '仓储费和查验等费用，保险费，海关查验费，仓储费，待时费，快递杂费实报实销', 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (13, 8, '融迅', '空运', '一般贸易', NULL, '7天', '深圳-香港1-2天，香港-新加坡4-5天，全程：5-7天，海关查验顺延', '保险费，海关查验费，国内转运费，二次包装费，新加坡仓储费，待时费，香港杂费实报实销', 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (14, 8, '一般贸易过港+双清方案', '空运', '一般贸易+双清', NULL, '7天', '深圳-香港1-2天，香港-新加坡4-5天，全程：5-7天，海关查验顺延', '保险费，海关查验费，国内转运费，二次包装费，新加坡仓储费，待时费，香港杂费实报实销', 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (15, 9, '越海速达', NULL, '双清', '双清', '6天', '起运后4-6天，海关查验顺延', '保险费，海关查验费，国内转运费，二次包装费，超重和超尺费', 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (16, 11, '融迅', NULL, '双清', '双清含税报价', '20天', '时效10-15个工作日左右；全程15-20天，海关查验顺延', '保险费，包装费，国内转运费，海关查验费，仓储费，待时费', 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (17, 12, '融迅', '快递', '贸易代理', '快递+贸代方案', '12天', '提货+包装需要2-3天，快递4-6天，拼车时效：2-3天（从荷兰发运-德国法兰克福），全程：8-12天，海关查验顺延', '不含卸货上楼，如果需要卸货上楼，需要准备地址： EUR 200 预估                                             不含仓储费和查验等费用，保险费，海关查验费，仓储费，待时费，快递杂费实报实销', 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (18, 13, '融迅', '空运', NULL, '预估', '7天', '起运后5-7 个工作日，海关查验顺延', '仓储费，查验费，待时费等其他额外费用，保险费，海关查验费，仓储费，待时费，验电费，香港杂费实报实销', 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (19, 14, '融迅', '空运', '正清', NULL, '6天', '起运后4-6天，海关查验顺延', '保险费，海关查验费，仓储费，香港杂费实报实销，', 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (20, 15, '融迅', '空运', '专线', NULL, '7天', '时效2-4个工作日，再转当地派送1-3个工作日；起运后：4-7个工作日左右，海关查验顺延', '不含回收垃圾，保险、香港本地杂费等，保险费，海关查验费，二次包装费，香港杂费实报实销，拆托+回收垃圾，不含香港提货，入仓登记费等', 1, '专线有海关查验或者扣货风险，只能赔付运费，请知悉.', '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (21, 15, '启文', '快递', '专线', NULL, '7天', '起运后：5-7个工作日左右，海关查验顺延', '保险费，海关查验费，二次包装费，香港杂费实报实销，拆托+回收垃圾，不含香港提货，入仓登记费等', 1, '专线有海关查验或者扣货风险，只能赔付运费，请知悉.', '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (22, 16, '融迅', NULL, '专线', NULL, '8天', '约6-8工作日，如遇海关查验时间顺延', '香港本地杂费，香港杂费实报实销，尾端是当地物流派送，做不了额外操作，无指定签收单，不含预约备案，卸货上楼回收垃圾等费用，如果需要的话，先按卸货上楼：USD250，回收垃圾：USD200预估，需要有具体地址后再确认，二次包装费，保险费，存储费、送货时的卡车等待费、停车费等，无签收单，如产生其他费用实报实销', 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (23, 17, '嘉里', NULL, '一般贸易', NULL, '8天', '深圳-香港预计2天时间，香港-日本预计4-6天，预计全程6-8天，海关查验顺延', '保险费，国内中转费，香港杂费实报实销，不含日本拆托+回收垃圾，待时费,海关查验费', 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (24, 17, '融迅', '空运', '一般贸易', NULL, '8天', '深圳-香港预计2天时间，香港-日本预计4-6天，预计全程6-8天，海关查验顺延', '保险费，国内中转费，香港杂费实报实销，不含日本拆托+回收垃圾，待时费,海关查验费，机场保税仓费用,仓储费', 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (25, 19, '银顺达', '空派', '专线', '专线方案', '15天', '双清包税专线：12-15天左右；展会物资需要提前，不保证时效，如遇海关查验时间顺延', '北京-深圳的运输费用，保险费，二次包装费，存储费，送货时的卡车等待费、停车费、回收垃圾的费用，及海关查验产生的相关费用等，如产生其他费用实报实销', 1, '不退运费，40/KG', '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (26, 19, '银顺达', '快递', '专线', '快递方案', '6天', 'DHL：  6天左右；展会物资需要提前，不保证时效，如遇海关查验时间顺延', '北京-深圳的运输费用，保险费，二次包装费，存储费，送货时的卡车等待费、停车费、回收垃圾的费用，及海关查验产生的相关费用等，如产生其他费用实报实销', 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (27, 22, '华平', '陆运', '双清', '专线   协议过期，未合作过', '12天', '专线10-12工作日左右， 不提供税单等文件；一般贸易出口放行后10-12工作日左右；如海关查验时间顺延', '保险费，需要提供货值/卸货费/二次包装费及其他实报实销费用', 1, '陆运灰清的，未购买保险，丢失按运费3-5倍赔偿，如果需要，保险可以按货值3%购买，如果丢失，全赔。', '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (28, 22, '越海专线', '陆运', '双清', NULL, '12天', '专线10-12工作日左右， 不提供税单等文件；一般贸易出口放行后10-12工作日左右；如海关查验时间顺延', '保险费，需要提供货值/卸货费/二次包装费及其他实报实销费用', 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (29, 22, '华平', NULL, '正清', '正清', '12天', '专线10-12工作日左右， 不提供税单等文件；一般贸易出口放行后10-12工作日左右；如海关查验时间顺延', '收货人缴纳， 如上报价不含税金，保险费，需要提供货值，国外税金，保险费，需要提供货值/卸货费/二次包装费及其他实报实销费用', 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (30, 23, '华平', '陆运', '专线', '专线   协议过期，未合作过', '12天', '专线10-12工作日左右， 不提供税单等文件， 以实际为准；一般贸易出口放行后10-12工作日左右，以实际为准；如海关查验时间顺延', '保险费，需要提供货值/卸货费/二次包装费及其他实报实销费用', 1, '陆运灰清的，未购买保险，丢失按运费3-5倍赔偿，如果需要，保险可以按货值3%购买，如果丢失，全赔。', '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (31, 23, '越海专线', NULL, NULL, NULL, '12天', '专线10-12工作日左右， 不提供税单等文件， 以实际为准；一般贸易出口放行后10-12工作日左右，以实际为准；如海关查验时间顺延', '保险费，需要提供货值/卸货费/二次包装费及其他实报实销费用', 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (32, 23, '华平', '陆运', '正清', '正清', '12天', '专线10-12工作日左右， 不提供税单等文件， 以实际为准；一般贸易出口放行后10-12工作日左右，以实际为准；如海关查验时间顺延', '税金实报实销， 请收货人缴纳， 如上报价不含税金（客户没提供货值），国外税金，保险费，需要提供货值/卸货费/二次包装费及其他实报实销费用', 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (33, 10, '贸易代理方案', '空运', '贸易代理', NULL, NULL, NULL, '不含包装费，北京提货费至深圳费用，不含周末清关提货费，不含回收垃圾的费用，保险费', 0, NULL, '2026-02-25 18:09:23');
INSERT INTO `route_agents` VALUES (144, 110, '融迅', '空运', '一般贸易', '555', '7天', '222', '333', 1, '444', '2026-03-11 11:00:07');
INSERT INTO `route_agents` VALUES (145, 107, '融迅', '空运', '一般贸易', '555', '7天', '222', '333', 1, '444', '2026-03-11 14:57:01');
INSERT INTO `route_agents` VALUES (146, 109, '融迅', '空运', '一般贸易', '666', '8天', '333', '444', 1, '555', '2026-03-11 17:43:33');

-- ----------------------------
-- Table structure for routes
-- ----------------------------
DROP TABLE IF EXISTS `routes`;
CREATE TABLE `routes`  (
  `路线ID` int NOT NULL AUTO_INCREMENT,
  `起始地` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `途径地` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `目的地` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `交易开始日期` date NULL DEFAULT NULL COMMENT '交易周期开始日期',
  `交易结束日期` date NULL DEFAULT NULL COMMENT '交易周期结束日期',
  `交易年份` year GENERATED ALWAYS AS (year(`交易开始日期`)) STORED COMMENT '虚拟列:交易年份' NULL,
  `交易月份` tinyint GENERATED ALWAYS AS (month(`交易开始日期`)) STORED COMMENT '虚拟列:交易月份' NULL,
  `实际重量(/kg)` decimal(18, 2) NULL DEFAULT 0.00 COMMENT '路线总实际重量,单位:千克',
  `计费重量(/kg)` decimal(18, 2) NULL DEFAULT NULL COMMENT '路线计费重量,单位:千克',
  `总体积(/cbm)` decimal(18, 3) NULL DEFAULT NULL COMMENT '路线总体积,单位:立方米',
  `货值` decimal(18, 2) NULL DEFAULT 0.00,
  `货物名称` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '汇总的货物名称列表',
  `创建时间` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`路线ID`) USING BTREE,
  INDEX `idx_start_date`(`交易开始日期` ASC) USING BTREE COMMENT '交易开始日期索引',
  INDEX `idx_end_date`(`交易结束日期` ASC) USING BTREE COMMENT '交易结束日期索引',
  INDEX `idx_year_month`(`交易年份` ASC, `交易月份` ASC) USING BTREE COMMENT '年月查询优化索引',
  INDEX `idx_origin`(`起始地` ASC) USING BTREE COMMENT '起始地索引',
  INDEX `idx_destination`(`目的地` ASC) USING BTREE COMMENT '目的地索引'
) ENGINE = InnoDB AUTO_INCREMENT = 111 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of routes
-- ----------------------------
INSERT INTO `routes` VALUES (1, '国内', NULL, '西班牙', '2025-10-20', '2025-10-24', DEFAULT, DEFAULT, 1740.00, 1740.00, 0.000, 0.00, '碱性电池', '2026-02-25 18:09:23');
INSERT INTO `routes` VALUES (2, '深圳', NULL, '新加坡', '2025-10-20', '2025-10-24', DEFAULT, DEFAULT, 910.00, 910.00, 5.460, 100000.00, '2件展示柜', '2026-02-25 18:09:23');
INSERT INTO `routes` VALUES (3, '深圳', NULL, '英国', '2025-10-20', '2025-10-24', DEFAULT, DEFAULT, 910.00, 910.00, 5.460, 100000.00, '2件展示柜', '2026-02-25 18:09:23');
INSERT INTO `routes` VALUES (4, '国内', NULL, '澳门', '2025-10-20', '2025-10-24', DEFAULT, DEFAULT, 930.00, 930.00, 2.734, 0.00, '2件展示柜, 电子屏, 粮食标本, 酿酒陶坛', '2026-02-25 18:09:23');
INSERT INTO `routes` VALUES (5, '深圳', NULL, '澳洲', '2025-10-20', '2025-10-24', DEFAULT, DEFAULT, NULL, NULL, NULL, NULL, NULL, '2026-02-25 18:09:23');
INSERT INTO `routes` VALUES (6, '深圳', NULL, '香港', '2025-10-20', '2025-10-24', DEFAULT, DEFAULT, NULL, NULL, NULL, NULL, NULL, '2026-02-25 18:09:23');
INSERT INTO `routes` VALUES (7, '达拉斯', NULL, '新加坡', '2025-10-20', '2025-10-24', DEFAULT, DEFAULT, 10.00, 10.00, NULL, 12000.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `routes` VALUES (8, '深圳', NULL, '新加坡', '2025-10-20', '2025-10-24', DEFAULT, DEFAULT, 100.00, 100.00, NULL, 571262.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `routes` VALUES (9, '深圳', NULL, '新加坡', '2025-10-20', '2025-10-24', DEFAULT, DEFAULT, 30.00, 30.00, NULL, 37928.30, NULL, '2026-02-25 18:09:23');
INSERT INTO `routes` VALUES (10, '香港', NULL, '达拉斯', '2025-10-20', '2025-10-24', DEFAULT, DEFAULT, 30.00, 45.00, NULL, 266338.80, NULL, '2026-02-25 18:09:23');
INSERT INTO `routes` VALUES (11, '国内', NULL, '法兰克福', '2025-10-20', '2025-10-24', DEFAULT, DEFAULT, 100.00, 100.00, NULL, 677863.35, NULL, '2026-02-25 18:09:23');
INSERT INTO `routes` VALUES (12, '达拉斯', NULL, '法兰克福', '2025-10-20', '2025-10-24', DEFAULT, DEFAULT, 8.00, 8.00, NULL, 11906.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `routes` VALUES (13, '香港', NULL, '新加坡', '2025-10-20', '2025-10-24', DEFAULT, DEFAULT, 100.00, 100.00, NULL, 75124.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `routes` VALUES (14, '香港', NULL, '马来', '2025-10-20', '2025-10-24', DEFAULT, DEFAULT, 30.00, 45.00, NULL, 92000.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `routes` VALUES (15, '香港', NULL, '马来', '2025-10-20', '2025-10-24', DEFAULT, DEFAULT, 20.00, 30.00, NULL, NULL, NULL, '2026-02-25 18:09:23');
INSERT INTO `routes` VALUES (16, '香港', NULL, '菲律宾马尼拉', '2025-10-20', '2025-10-24', DEFAULT, DEFAULT, 150.00, 150.00, 0.000, 0.00, '4台Dell PowerEdge R7625', '2026-02-25 18:09:23');
INSERT INTO `routes` VALUES (17, '深圳', '香港', '日本', '2025-10-20', '2025-10-24', DEFAULT, DEFAULT, 2600.00, 3000.00, 15.000, NULL, NULL, '2026-02-25 18:09:23');
INSERT INTO `routes` VALUES (18, '新加坡', NULL, '马来西亚', '2025-10-20', '2025-10-24', DEFAULT, DEFAULT, NULL, NULL, NULL, NULL, NULL, '2026-02-25 18:09:23');
INSERT INTO `routes` VALUES (19, '北京', NULL, '沙特', '2025-10-20', '2025-10-24', DEFAULT, DEFAULT, 120.00, 120.00, 0.000, 0.00, '宣传册&伴手礼', '2026-02-25 18:09:23');
INSERT INTO `routes` VALUES (20, '国内', NULL, '荷兰', '2025-10-20', '2025-10-24', DEFAULT, DEFAULT, 20.20, 20.20, NULL, NULL, NULL, '2026-02-25 18:09:23');
INSERT INTO `routes` VALUES (21, '国内', NULL, '荷兰', '2025-10-20', '2025-10-24', DEFAULT, DEFAULT, 45.00, 45.00, NULL, NULL, NULL, '2026-02-25 18:09:23');
INSERT INTO `routes` VALUES (22, '上海', NULL, '越南', '2025-10-20', '2025-10-24', DEFAULT, DEFAULT, 0.00, 17000.00, 0.000, 0.00, '长雨伞和短雨伞', '2026-02-25 18:09:23');
INSERT INTO `routes` VALUES (23, '深圳', NULL, '越南', '2025-10-20', '2025-10-24', DEFAULT, DEFAULT, 0.00, 27000.00, 0.000, 0.00, '风扇', '2026-02-25 18:09:23');
INSERT INTO `routes` VALUES (107, '深圳', '香港', '新加坡', '2026-03-17', '2026-03-18', DEFAULT, DEFAULT, 40.00, 50.00, 5.000, 10000.00, '服务器, 服务器设备', '2026-03-11 10:13:06');
INSERT INTO `routes` VALUES (109, '深圳', '香港', '新加坡', '2026-03-09', '2026-03-10', DEFAULT, DEFAULT, 40.00, 60.00, 5.000, 10000.00, '服务器, 服务器设备', '2026-03-11 10:39:08');
INSERT INTO `routes` VALUES (110, '深圳', '香港', '美国圣何塞', '2026-02-03', '2026-02-04', DEFAULT, DEFAULT, 240.00, 240.00, 5.000, 100000.00, '交换机', '2026-03-11 10:48:00');

-- ----------------------------
-- Table structure for summary
-- ----------------------------
DROP TABLE IF EXISTS `summary`;
CREATE TABLE `summary`  (
  `汇总ID` int NOT NULL AUTO_INCREMENT,
  `代理路线ID` int NOT NULL,
  `小计` decimal(18, 2) NULL DEFAULT 0.00,
  `税率` decimal(10, 4) NULL DEFAULT 0.0000,
  `税金` decimal(18, 2) NULL DEFAULT 0.00,
  `汇损率` decimal(10, 6) NULL DEFAULT 0.000000,
  `汇损` decimal(18, 2) NULL DEFAULT 0.00,
  `总计` decimal(18, 2) NULL DEFAULT 0.00,
  `备注` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `创建时间` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`汇总ID`) USING BTREE,
  UNIQUE INDEX `unique_agent_route_id`(`代理路线ID` ASC) USING BTREE,
  INDEX `idx_agent_route_id`(`代理路线ID` ASC) USING BTREE,
  CONSTRAINT `fk_summary_route_agents` FOREIGN KEY (`代理路线ID`) REFERENCES `route_agents` (`代理路线ID`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 171 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of summary
-- ----------------------------
INSERT INTO `summary` VALUES (34, 1, 40020.00, NULL, 0.00, NULL, 0.00, 40020.00, '地址不偏远，不超尺寸，不超重参考此报价,不超尺和不超重的标准：长+宽+高<300CM，单边不得超过120CM,最小尺寸为15CM*10CM*2CM；MRW单件实重不超40KG，建议控制在25KG左右', '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (35, 2, 38280.00, NULL, 0.00, NULL, 0.00, 38280.00, '海运双清包税到门，不卸货上楼', '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (36, 3, 29580.00, NULL, 0.00, NULL, 0.00, 29580.00, '货交深圳，文件资质齐全可以出，双清包税到门,需要文件、资质齐全(MSDS等)', '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (37, 4, 2730.00, 0.0900, 9000.00, NULL, 0.00, 11730.00, '新加坡进口GST：9%', '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (38, 5, 2074.80, 0.0900, 9000.00, NULL, 0.00, 11074.80, '新加坡进口GST：9%', '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (39, 6, 13195.00, 0.2000, 20000.00, NULL, 0.00, 33195.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (41, 8, 4790.00, NULL, 0.00, NULL, 0.00, 4790.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (43, 10, 1100.00, NULL, 0.00, NULL, 0.00, 1100.00, '粮食标本不接,只能送到会展门口，可以指定日期送货，不能指定时间段送货。', '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (44, 11, 2700.00, NULL, 0.00, NULL, 0.00, 2700.00, '粮食标本只能少量出，量大涉政，数量变多了需要重新确认。可以送到展馆，可以指定日期和时间段送货', '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (45, 12, 4802.00, 0.0900, 1080.00, NULL, 0.00, 5882.00, '不含仓储费和查验等费用,UPS有其他杂费收取 实报实销', '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (46, 13, 7928.00, 0.0900, 51413.58, 0.040000, 22850.48, 82192.06, '备注：一般贸易过港需要发票，箱单，品牌授权', '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (47, 15, 2350.00, NULL, 0.00, NULL, 0.00, 2350.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (48, 16, 7800.00, 0.1900, 128794.04, NULL, 0.00, 136594.04, NULL, '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (49, 17, 1885.00, 0.1900, 2262.14, 0.040000, 476.24, 4623.38, 'Duty和VAT实报实销,UPS有其他杂费收取 实报实销', '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (50, 18, 7518.00, 0.0900, 6761.16, NULL, 0.00, 14279.16, '有效期：本周有效', '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (51, 19, 2643.50, 0.0500, 4600.00, 0.060000, 5520.00, 12763.50, '文件： 需要办理SIRIM， 英文说明书，发票，箱单，客户的账户密码，办理需要3-5个工作日', '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (52, 20, 1970.00, NULL, 0.00, NULL, 0.00, 1970.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (53, 21, 900.00, NULL, 0.00, NULL, 0.00, 900.00, '尾程快递服务+不能指定签收单，只有快递截图,不含卸货，拆托+回收垃圾', '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (54, 22, 11850.00, NULL, 0.00, NULL, 0.00, 11850.00, '诚哥建议税率,服务器出口菲律宾 HS CODE：8471.50.90 关税：0.00% 增值税12.50%', '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (55, 23, 99985.00, 0.1000, 0.00, 0.050000, 0.00, 99985.00, '文件： 发票，箱单，POA， 不需要其他认证', '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (56, 24, 824650.00, 0.1000, 0.00, 0.050000, 0.00, 824650.00, '文件： 发票，箱单，POA， 不需要其他认证', '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (57, 25, 7400.00, NULL, 0.00, NULL, 0.00, 7400.00, '双清包税专线，无牌不侵权,只能送展会门口，可以指定日期送货', '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (58, 26, 7680.00, NULL, 0.00, NULL, 0.00, 7680.00, '快递方案需要收货人配合清关、缴税以及提供所需文件,只能送展会门口，不可以指定日期送货.诚哥建议税号如下，有汇损，实报实销，以快递公司税单为准:宣传册 原产地：中国 出口至沙特 HS CODE：49.01.99.90.00.00 关税：0.00% 增值税：15.00%;丝巾 原产地：中国 出口至沙特 HS CODE：62.14.10.00.00.00 关税：5.00% 增值税：15.00%;丝绸扇子 原产地：中国 出口至沙特 HS CODE：63.07.90.99.00.00 关税：5.00% 增值税：15.00%;剪纸画轴 原产地：中国 出口至沙特 HS CODE：48.22.90.00.00.00 关税：5.00% 增值税：15.00%', '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (59, 27, 64760.00, NULL, 0.00, NULL, 0.00, 64760.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (60, 28, 100110.00, NULL, 0.00, NULL, 0.00, 100110.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (61, 29, 71210.00, NULL, 0.00, NULL, 0.00, 71210.00, '正清出口所需文件：发票箱单 授权委托书， 申报要素等全套清关文件,越南进口：需提前签署POA及其他清关文件', '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (62, 30, 87150.00, NULL, 0.00, NULL, 0.00, 87150.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (63, 31, 129000.00, NULL, 0.00, NULL, 0.00, 129000.00, NULL, '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (64, 32, 7100.00, NULL, 0.00, NULL, 0.00, 7100.00, '正清出口：发票箱单 授权委托书， 申报要素等全套清关文件，电池需要msds+陆运运输鉴定书（需要发货前先提供审核）,越南进口：需提前签署POA及其他清关文件,风扇越南需要做商检， 客户收货人做好， 如海关有其他要求也许配合', '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (65, 9, 500.00, NULL, 0.00, NULL, 0.00, 500.00, '备注：一般贸易过港需要发票，箱单，品牌授权', '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (66, 7, 10340.00, NULL, 0.00, NULL, 0.00, 10340.00, '备注：一般贸易过港需要发票，箱单，品牌授权', '2026-02-25 18:09:23');
INSERT INTO `summary` VALUES (168, 144, 2600.00, 0.0900, 9000.00, 0.040000, 4000.00, 15600.00, '888', '2026-03-11 11:00:07');
INSERT INTO `summary` VALUES (169, 145, 2200.00, 0.0900, 900.00, 0.040000, 400.00, 3500.00, '888', '2026-03-11 14:57:01');
INSERT INTO `summary` VALUES (170, 146, 2600.00, 0.0900, 900.00, 0.040000, 400.00, 3900.00, '999', '2026-03-11 17:43:33');

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
-- Records of users
-- ----------------------------
INSERT INTO `users` VALUES (1, 'admin', '$2b$12$0.XTND5NNtu28ZhCF2qMmu5pBI3kbqki3QTe32T86ix9C2DnXqe2a', '系统管理员', 'admin@company.com', 1, 1, '2026-02-12 13:54:14', '2026-02-12 13:54:14');
INSERT INTO `users` VALUES (2, 'user', '$2b$12$zbHcZMEvpoZuanh5xFrA9upXLNwRlSAsXOWhP2w7k/UyBRjpuAaOq', '测试用户', 'user@company.com', 1, 0, '2026-02-12 13:54:14', '2026-02-12 13:54:14');

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
    DECLARE v_route_id INT DEFAULT 0;
    DECLARE v_subtotal DECIMAL(18,2) DEFAULT 0;
    DECLARE v_tax_rate DECIMAL(10,4) DEFAULT 0;
    DECLARE v_tax DECIMAL(18,2) DEFAULT 0;
    DECLARE v_loss_rate DECIMAL(10,6) DEFAULT 0;
    DECLARE v_loss DECIMAL(18,2) DEFAULT 0;
    DECLARE v_total DECIMAL(18,2) DEFAULT 0;
    DECLARE v_route_value DECIMAL(18,2) DEFAULT 0;

    SELECT `路线ID` INTO v_route_id
    FROM route_agents
    WHERE `代理路线ID` = p_agent_route_id
    LIMIT 1;

    IF v_route_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '找不到对应的route_agents记录';
    END IF;

    SELECT IFNULL(`货值`,0) INTO v_route_value
    FROM routes
    WHERE `路线ID` = v_route_id
    LIMIT 1;

    SELECT 
        IFNULL(SUM(`人民币金额`),0)
    INTO v_subtotal
    FROM (
        SELECT `人民币金额` FROM fee_items WHERE `代理路线ID` = p_agent_route_id
        UNION ALL
        SELECT `人民币金额` FROM fee_total WHERE `代理路线ID` = p_agent_route_id
    ) combined_fees;

    SELECT 
        IFNULL(`税率`,0), 
        IFNULL(`汇损率`,0)
    INTO v_tax_rate, v_loss_rate
    FROM summary
    WHERE `代理路线ID` = p_agent_route_id
    LIMIT 1;

    SET v_tax = (v_subtotal + v_route_value) * (v_tax_rate / 100);
    SET v_loss = (v_subtotal + v_route_value) * (v_loss_rate / 100);
    SET v_total = v_subtotal + v_route_value + v_tax + v_loss;

    IF EXISTS(SELECT 1 FROM summary WHERE `代理路线ID` = p_agent_route_id) THEN
        UPDATE summary
        SET 
            `小计` = v_subtotal,
            `税金` = v_tax,
            `汇损` = v_loss,
            `总计` = v_total
        WHERE `代理路线ID` = p_agent_route_id;
    ELSE
        INSERT INTO summary(`代理路线ID`, `小计`, `税率`, `税金`, `汇损率`, `汇损`, `总计`)
        VALUES (p_agent_route_id, v_subtotal, v_tax_rate, v_tax, v_loss_rate, v_loss, v_total);
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
    
    -- 1. 计算小计（所有费用的人民币总和）
    SELECT COALESCE(SUM(人民币金额), 0) + COALESCE(
        (SELECT SUM(人民币金额) FROM fee_total WHERE 代理路线ID = NEW.代理路线ID), 0
    )
    INTO total_fee
    FROM fee_items
    WHERE 代理路线ID = NEW.代理路线ID;
    
    -- 2. 获取该代理路线对应的routes.货值
    SELECT r.货值
    INTO route_value
    FROM routes r
    INNER JOIN route_agents ra ON r.路线ID = ra.路线ID
    WHERE ra.代理路线ID = NEW.代理路线ID;
    
    -- 3. 设置计算结果
    SET NEW.小计 = total_fee;
    SET NEW.税金 = COALESCE(route_value, 0) * COALESCE(NEW.税率, 0);  -- ✅ 修复：使用货值
    SET NEW.汇损 = COALESCE(route_value, 0) * COALESCE(NEW.汇损率, 0);  -- ✅ 修复：使用货值
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
    
    -- 1. 计算小计（所有费用的人民币总和）
    SELECT COALESCE(SUM(人民币金额), 0) + COALESCE(
        (SELECT SUM(人民币金额) FROM fee_total WHERE 代理路线ID = NEW.代理路线ID), 0
    )
    INTO total_fee
    FROM fee_items
    WHERE 代理路线ID = NEW.代理路线ID;
    
    -- 2. 获取该代理路线对应的routes.货值
    SELECT r.货值
    INTO route_value
    FROM routes r
    INNER JOIN route_agents ra ON r.路线ID = ra.路线ID
    WHERE ra.代理路线ID = NEW.代理路线ID;
    
    -- 3. 设置计算结果
    SET NEW.小计 = total_fee;
    SET NEW.税金 = COALESCE(route_value, 0) * COALESCE(NEW.税率, 0);  -- ✅ 修复：使用货值
    SET NEW.汇损 = COALESCE(route_value, 0) * COALESCE(NEW.汇损率, 0);  -- ✅ 修复：使用货值
    SET NEW.总计 = NEW.小计 + NEW.税金 + NEW.汇损;
END
;;
delimiter ;

SET FOREIGN_KEY_CHECKS = 1;
