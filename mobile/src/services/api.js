const API_BASE_URL = 'http://your-api-url/api/v1';

export const uploadAudio = async (audioFile) => {
  const formData = new FormData();
  formData.append('file', {
    uri: audioFile.uri,
    type: 'audio/m4a',
    name: 'recording.m4a',
  });

  try {
    const response = await fetch(`${API_BASE_URL}/audio/upload`, {
      method: 'POST',
      body: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return await response.json();
  } catch (error) {
    console.error('Error uploading audio:', error);
    throw error;
  }
};

export const checkStatus = async (jobId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/audio/status/${jobId}`);
    return await response.json();
  } catch (error) {
    console.error('Error checking status:', error);
    throw error;
  }
}; 