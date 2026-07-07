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

import type {
  directions,
  imageModelOptions,
  imageRatioOptions,
  imageResolutionOptions,
  settingsSections,
  skillCategories,
} from './data';

export type ConvHistory = { id: number; title: string; node_id: string; direction: string; message_count: number; created_at: string; updated_at: string };
export type Direction = (typeof directions)[number];
export type ImageModelId = (typeof imageModelOptions)[number];
export type ImageRatio = (typeof imageRatioOptions)[number];
export type ImageResolution = (typeof imageResolutionOptions)[number];
export type ToastVariant = 'success' | 'error' | 'info';
export type ToastInput = {
  message: string;
  title?: string;
  variant?: ToastVariant;
  duration?: number;
};
export type ShowToast = (toast: ToastInput | string) => void;
export type SettingsSection = (typeof settingsSections)[number];
export type SidebarPage = 'home' | 'skills' | 'projects' | 'settings' | 'image' | 'video' | 'coding';
export type CreativeMode = 'image' | 'video' | 'coding';
export type ProjectView = 'home' | 'folder' | 'ai' | 'uploaded' | 'detail';
export type ProjectModal = 'new-folder' | 'upload' | 'rename-folder' | 'rename-file' | null;
export type SkillView = 'market' | 'installed';
export type SkillModal = 'custom' | 'detail' | 'manage' | 'install' | 'external' | null;
export type SkillCategory = (typeof skillCategories)[number];
export type PickerType = 'model' | 'image-mode' | 'image-model' | null;
export type LibraryModalType = 'file' | 'skill' | null;

export type ProjectFolder = {
  name: string;
  count?: string;
  desc: string;
  tone: string;
  locked?: boolean;
  deletable?: boolean;
  modified?: string;
};

export type ProjectFile = {
  name: string;
  folder: string;
  type: string;
  size: number;
  modified: string;
  url: string;
  source: 'manual_upload' | 'ai' | 'system' | string;
};

export type ProjectImage = {
  name: string;
  url: string;
  size: number;
  modified: string;
  prompt?: string;
  style?: string;
  model?: string;
  ratio?: string;
  resolution?: string;
  source?: string;
  reference_count?: number;
  created_at?: string;
};

export type SkillSource = 'market' | 'external' | 'custom';

export type SkillLibraryItem = {
  id: string;
  name: string;
  description: string;
  category: string;
  full_content: string;
  source: SkillSource;
  tone?: string;
  doc?: string;
  version?: string;
  entry_file?: string;
  connection?: string;
  created_at?: string;
};

export type CustomSkillInput = {
  name: string;
  category: string;
  description: string;
  connection: string;
};
