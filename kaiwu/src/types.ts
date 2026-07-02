/**
 * =============================================================================
 * # 角色
 * 类型定义层 —— 为曜势科技 App 提供所有 TypeScript 类型约束。
 * 从 data.ts 中的常量派生联合类型，同时定义组件状态、视图模式、
 * 模态框类型等枚举类型。
 *
 * # 输入
 * - data.ts 中的 `directions`、`settingsSections`、`skillCategories` 常量
 * - 组件的状态设计文档
 *
 * # 输出结构
 * ## 1. 对话历史类型
 * ConvHistory —— 单条对话记录的完整字段类型
 *
 * ## 2. 常量派生类型
 * Direction —— 赛道方向联合类型（从 directions 派生）
 * SettingsSection —— 设置页签联合类型（从 settingsSections 派生）
 * SkillCategory —— 技能分类联合类型（从 skillCategories 派生）
 *
 * ## 3. 视图/模态枚举类型
 * SidebarPage | ProjectView | ProjectModal | SkillView | SkillModal
 *
 * ## 4. 交互状态类型
 * PickerType | LibraryModalType
 * =============================================================================
 */

import type { directions, settingsSections, skillCategories } from './data';

export type ConvHistory = { id: number; title: string; node_id: string; direction: string; message_count: number; created_at: string; updated_at: string };
export type Direction = (typeof directions)[number];
export type SettingsSection = (typeof settingsSections)[number];
export type SidebarPage = 'home' | 'skills' | 'projects' | 'settings' | 'image' | 'video' | 'coding';
export type ProjectView = 'home' | 'folder' | 'ai' | 'uploaded';
export type ProjectModal = 'new-folder' | 'upload' | 'file-detail' | 'folder-detail' | null;
export type SkillView = 'market' | 'installed';
export type SkillModal = 'custom' | 'detail' | 'manage' | 'install' | 'external' | null;
export type SkillCategory = (typeof skillCategories)[number];
export type PickerType = 'model' | null;
export type LibraryModalType = 'file' | 'skill' | null;
