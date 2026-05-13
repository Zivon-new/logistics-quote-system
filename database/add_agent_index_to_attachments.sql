-- 给 route_attachments 表新增 agent_index 字段，用于区分各代理商附件
-- agent_index: 0 起始，NULL 表示路线级附件（历史数据兼容）
ALTER TABLE route_attachments
  ADD COLUMN agent_index INT DEFAULT NULL COMMENT '代理商序号（0起始）';
