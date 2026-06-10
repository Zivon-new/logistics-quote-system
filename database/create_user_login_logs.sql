-- 新增登录历史日志表：记录每次成功登录的用户、时间、来源 IP，供 admin 主页查看历史登录记录
CREATE TABLE `user_login_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `login_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `ip_address` varchar(45) NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `ix_user_login_logs_login_at` (`login_at`),
  CONSTRAINT `fk_user_login_logs_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;
