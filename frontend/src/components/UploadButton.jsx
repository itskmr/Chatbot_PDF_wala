import React from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';

const UploadButton = ({ setPdfUploaded }) => {
  const handleUpload = async (event) => {
    const file = event.target.files[0];
    if (!file || !file.name.endsWith('.pdf')) {
      toast.error('Please upload a valid PDF file.');
      return;
    }

    const formData = new FormData();
    formData.append('pdf_file', file);

    try {
      const response = await axios.post('http://localhost:5000/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      toast.success(response.data.message);
      setPdfUploaded(true);
    } catch (error) {
      toast.error(error.response?.data?.error || 'Error uploading file.');
    }
  };

  return (
    <div className="mb-4">
      <input
        type="file"
        id="pdf-upload"
        accept=".pdf"
        onChange={handleUpload}
        className="hidden"
      />
      <label
        htmlFor="pdf-upload"
        className="inline-block px-4 py-2 bg-gray-200 rounded-full cursor-pointer hover:bg-gray-300"
      >
        ⬆ Upload a PDF
      </label>
    </div>
  );
};

export default UploadButton;