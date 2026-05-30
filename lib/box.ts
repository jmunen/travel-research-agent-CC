import type { BoxSaveResult } from './types';

function getBoxAccessToken() {
  const token = process.env.BOX_ACCESS_TOKEN;

  if (!token) {
    throw new Error('Missing BOX_ACCESS_TOKEN in .env.local');
  }

  return token;
}

function getBoxParentFolderId() {
  return process.env.BOX_FOLDER_ID || '0';
}

function safeFileName(destination: string): string {
  const cleanDestination = destination
    .trim()
    .replace(/[^a-z0-9]/gi, '_')
    .replace(/_+/g, '_');

  const today = new Date().toISOString().slice(0, 10);

  return `${cleanDestination}_Travel_Brief_${today}.md`;
}

async function createBoxFolder(folderName: string): Promise<string> {
  const response = await fetch('https://api.box.com/2.0/folders', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${getBoxAccessToken()}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      name: folderName,
      parent: {
        id: getBoxParentFolderId(),
      },
    }),
  });

  const data = await response.json();

  if (response.ok) {
    return data.id;
  }

  if (response.status === 409) {
    console.warn('Box folder already exists. Falling back to parent folder.');
    return getBoxParentFolderId();
  }

  throw new Error(`Failed to create Box folder: ${JSON.stringify(data)}`);
}

async function uploadMarkdownToBox(params: {
  folderId: string;
  fileName: string;
  content: string;
}): Promise<{ fileId: string; fileName: string }> {
  const formData = new FormData();

  formData.append(
    'attributes',
    JSON.stringify({
      name: params.fileName,
      parent: {
        id: params.folderId,
      },
    })
  );

  const fileBlob = new Blob([params.content], {
    type: 'text/markdown',
  });

  formData.append('file', fileBlob, params.fileName);

  const response = await fetch('https://upload.box.com/api/2.0/files/content', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${getBoxAccessToken()}`,
    },
    body: formData,
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(`Failed to upload file to Box: ${JSON.stringify(data)}`);
  }

  const uploadedFile = data.entries?.[0];

  return {
    fileId: uploadedFile.id,
    fileName: uploadedFile.name,
  };
}

async function createSharedLink(fileId: string): Promise<string | null> {
  const response = await fetch(`https://api.box.com/2.0/files/${fileId}`, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${getBoxAccessToken()}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      shared_link: {
        access: 'open',
      },
    }),
  });

  const data = await response.json();

  if (!response.ok) {
    console.warn('Could not create Box shared link:', data);
    return null;
  }

  return data.shared_link?.url || null;
}

export async function saveTravelBriefToBox(params: {
  destination: string;
  briefMarkdown: string;
}): Promise<BoxSaveResult> {
  try {
    const fileName = safeFileName(params.destination);

    const folderId = await createBoxFolder('Travel Research Agent');

    const uploaded = await uploadMarkdownToBox({
      folderId,
      fileName,
      content: params.briefMarkdown,
    });

    const boxUrl = await createSharedLink(uploaded.fileId);

    return {
      boxSaved: true,
      boxFileName: uploaded.fileName,
      boxUrl,
    };
  } catch (error) {
    console.error(error);

    return {
      boxSaved: false,
      boxFileName: null,
      boxUrl: null,
      error: error instanceof Error ? error.message : 'Unknown Box error',
    };
  }
}