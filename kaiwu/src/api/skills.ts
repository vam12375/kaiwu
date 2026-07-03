import { apiJson } from './client';
import type { SkillLibraryItem } from '../types';

export type ExternalSkill = SkillLibraryItem & {
  source: 'external';
};

export function fetchExternalSkills() {
  return apiJson<ExternalSkill[]>('/api/skills');
}
