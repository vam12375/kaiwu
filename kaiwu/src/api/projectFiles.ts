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

type RenameProjectFolderResponse = CreateProjectFolderResponse;

type UploadProjectFileResponse = {
  status: string;
  file: ProjectFile;
};

type RenameProjectFileResponse = UploadProjectFileResponse;

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

export function renameProjectFolder(folder: string, payload: ProjectFolderPayload) {
  return apiJson<RenameProjectFolderResponse>(`/api/project-folders/${encodeURIComponent(folder)}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
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

export function renameProjectFile(file: ProjectFile, name: string) {
  return apiJson<RenameProjectFileResponse>('/api/project-files', {
    method: 'PATCH',
    body: JSON.stringify({
      folder: file.folder,
      filename: file.name,
      name,
    }),
  });
}

export function deleteProjectFile(file: ProjectFile) {
  return apiJson<{ status: string; folder: string; filename: string }>('/api/project-files', {
    method: 'DELETE',
    body: JSON.stringify({
      folder: file.folder,
      filename: file.name,
    }),
  });
}

export function deleteProjectImages(names: string[]) {
  return apiJson<{ status: string; deleted: string[] }>('/api/project-images', {
    method: 'DELETE',
    body: JSON.stringify({ names }),
  });
}
