import { apiJson } from './client';
import type { ProjectFile, ProjectFolder } from '../types';

export type ProjectFolderPayload = {
  name: string;
  desc: string;
};

type CreateProjectFolderResponse = {
  status: string;
  folder: Omit<ProjectFolder, 'tone'>;
};

type UploadProjectFileResponse = {
  status: string;
  file: ProjectFile;
};

function readFileAsBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result;
      if (typeof result !== 'string') {
        reject(new Error('File read failed'));
        return;
      }
      resolve(result.split(',')[1] || '');
    };
    reader.onerror = () => reject(reader.error || new Error('File read failed'));
    reader.readAsDataURL(file);
  });
}

export function fetchProjectFiles(folder?: string) {
  const query = folder ? `?folder=${encodeURIComponent(folder)}` : '';
  return apiJson<ProjectFile[]>(`/api/project-files${query}`);
}

export function fetchProjectFolders() {
  return apiJson<Array<Omit<ProjectFolder, 'tone'>>>('/api/project-folders');
}

export function createProjectFolder(payload: ProjectFolderPayload) {
  return apiJson<CreateProjectFolderResponse>('/api/project-folders', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function deleteProjectFolder(folder: string) {
  return apiJson<{ status: string; folder: string }>(`/api/project-folders/${encodeURIComponent(folder)}`, {
    method: 'DELETE',
  });
}

export async function uploadProjectFile(file: File, folder: string) {
  const content = await readFileAsBase64(file);
  return apiJson<UploadProjectFileResponse>('/api/project-library/upload', {
    method: 'POST',
    body: JSON.stringify({
      filename: file.name,
      folder,
      content,
      base64: true,
    }),
  });
}
