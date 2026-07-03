import { useCallback, useEffect, useMemo, useState } from 'react';

import { fetchExternalSkills, type ExternalSkill } from '../api/skills';
import { installedSkills, skillMarketItems } from '../data';
import type { CustomSkillInput, SkillLibraryItem } from '../types';

const STORAGE_KEYS = {
  installed: 'kaiwu.skillLibrary.installed',
  enabled: 'kaiwu.skillLibrary.enabled',
  custom: 'kaiwu.skillLibrary.custom',
} as const;

const defaultInstalledSkillIds = installedSkills.map((name) => createMarketSkillId(name));

function createMarketSkillId(name: string) {
  return `market:${name}`;
}

function createExternalSkillId(id: string) {
  return `external:${id}`;
}

function normalizeSkillName(name: string) {
  return name.trim().toLowerCase();
}

function safeReadJson<T>(key: string, fallback: T, guard: (value: unknown) => value is T): T {
  if (typeof window === 'undefined') return fallback;
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return fallback;
    const value = JSON.parse(raw) as unknown;
    return guard(value) ? value : fallback;
  } catch {
    return fallback;
  }
}

function safeWriteJson(key: string, value: unknown) {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Browser storage can be full or disabled; the UI can still work in-memory.
  }
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === 'string');
}

function isSkillLibraryItem(value: unknown): value is SkillLibraryItem {
  if (!value || typeof value !== 'object') return false;
  const item = value as Record<string, unknown>;
  return (
    typeof item.id === 'string'
    && typeof item.name === 'string'
    && typeof item.description === 'string'
    && typeof item.category === 'string'
    && typeof item.full_content === 'string'
    && item.source === 'custom'
  );
}

function isCustomSkillArray(value: unknown): value is SkillLibraryItem[] {
  return Array.isArray(value) && value.every(isSkillLibraryItem);
}

function frontmatterValue(value: string) {
  return value.replace(/\r?\n/g, ' ').replace(/"/g, '\\"').trim();
}

function buildSkillContent(input: CustomSkillInput) {
  const name = frontmatterValue(input.name);
  const description = frontmatterValue(input.description);
  const category = frontmatterValue(input.category);
  const connection = frontmatterValue(input.connection);
  return `---
name: ${name}
description: ${description}
category: ${category}
connection: ${connection}
source: kaiwu-custom
---

# ${input.name}

${input.description}

## 连接方式

${input.connection || '本地技能说明'}
`;
}

function buildMarketSkillContent(skill: { name: string; desc: string; category: string; doc?: string }) {
  const description = skill.doc ?? skill.desc;
  return `---
name: ${frontmatterValue(skill.name)}
description: ${frontmatterValue(description)}
category: ${frontmatterValue(skill.category)}
source: kaiwu-market
---

# ${skill.name}

${description}
`;
}

export function useSkillLibrary() {
  const [externalSkills, setExternalSkills] = useState<ExternalSkill[]>([]);
  const [installedSkillIds, setInstalledSkillIds] = useState<string[]>(() => (
    safeReadJson(STORAGE_KEYS.installed, defaultInstalledSkillIds, isStringArray)
  ));
  const [enabledSkillIds, setEnabledSkillIds] = useState<string[]>(() => (
    safeReadJson(STORAGE_KEYS.enabled, defaultInstalledSkillIds, isStringArray)
  ));
  const [customSkills, setCustomSkills] = useState<SkillLibraryItem[]>(() => (
    safeReadJson(STORAGE_KEYS.custom, [], isCustomSkillArray)
  ));
  const [skillSearchQuery, setSkillSearchQuery] = useState('');

  useEffect(() => {
    fetchExternalSkills()
      .then(setExternalSkills)
      .catch(() => setExternalSkills([]));
  }, []);

  useEffect(() => {
    safeWriteJson(STORAGE_KEYS.installed, installedSkillIds);
  }, [installedSkillIds]);

  useEffect(() => {
    safeWriteJson(STORAGE_KEYS.enabled, enabledSkillIds);
  }, [enabledSkillIds]);

  useEffect(() => {
    safeWriteJson(STORAGE_KEYS.custom, customSkills);
  }, [customSkills]);

  const skillItems = useMemo<SkillLibraryItem[]>(() => {
    const items = skillMarketItems.map<SkillLibraryItem>((skill) => ({
      id: createMarketSkillId(skill.name),
      name: skill.name,
      description: skill.desc,
      category: skill.category,
      full_content: buildMarketSkillContent(skill),
      source: 'market',
      tone: skill.tone,
      doc: skill.doc,
    }));

    const marketIndexByName = new Map(
      items.map((item, index) => [normalizeSkillName(item.name), index]),
    );

    externalSkills.forEach((skill) => {
      const marketIndex = marketIndexByName.get(normalizeSkillName(skill.name));
      if (marketIndex !== undefined) {
        items[marketIndex] = {
          ...items[marketIndex],
          description: items[marketIndex].description || skill.description,
          full_content: skill.full_content || items[marketIndex].full_content,
          version: skill.version,
          entry_file: skill.entry_file,
        };
        return;
      }

      items.push({
        ...skill,
        id: createExternalSkillId(skill.id),
        category: skill.category || '方法论',
        source: 'external',
        tone: skill.tone || 'indigo',
      });
    });

    return [...items, ...customSkills];
  }, [customSkills, externalSkills]);

  const installSkill = useCallback((skillId: string) => {
    setInstalledSkillIds((current) => (
      current.includes(skillId) ? current : [...current, skillId]
    ));
    setEnabledSkillIds((current) => (
      current.includes(skillId) ? current : [...current, skillId]
    ));
  }, []);

  const uninstallSkill = useCallback((skillId: string) => {
    setInstalledSkillIds((current) => current.filter((id) => id !== skillId));
    setEnabledSkillIds((current) => current.filter((id) => id !== skillId));
    if (skillId.startsWith('custom:')) {
      setCustomSkills((current) => current.filter((skill) => skill.id !== skillId));
    }
  }, []);

  const toggleSkillEnabled = useCallback((skillId: string) => {
    setEnabledSkillIds((current) => {
      if (current.includes(skillId)) {
        return current.filter((id) => id !== skillId);
      }
      if (!installedSkillIds.includes(skillId)) {
        return current;
      }
      return [...current, skillId];
    });
  }, [installedSkillIds]);

  const saveCustomSkill = useCallback((input: CustomSkillInput) => {
    const name = input.name.trim();
    if (!name) return null;

    const id = `custom:${typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36)}`;
    const skill: SkillLibraryItem = {
      id,
      name,
      description: input.description.trim() || '自定义技能',
      category: input.category,
      connection: input.connection.trim(),
      full_content: buildSkillContent({ ...input, name }),
      source: 'custom',
      tone: 'teal',
      created_at: new Date().toISOString(),
    };

    setCustomSkills((current) => [skill, ...current]);
    setInstalledSkillIds((current) => [id, ...current.filter((item) => item !== id)]);
    setEnabledSkillIds((current) => [id, ...current.filter((item) => item !== id)]);
    return skill;
  }, []);

  return {
    customSkills,
    enabledSkillIds,
    externalSkills,
    installedSkillIds,
    installSkill,
    saveCustomSkill,
    setSkillSearchQuery,
    skillItems,
    skillSearchQuery,
    toggleSkillEnabled,
    uninstallSkill,
  };
}
