import React, { useState, useRef } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';

const ChatInput = ({ 
  setMessages, 
  pdfUploaded, 
  setPdfUploaded, 
  setUploadedFile,
  isUploading,
  setIsUploading
}) => {
  const [question, setQuestion] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const fileInputRef = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim() || isSubmitting) return;

    setMessages((prev) => [...prev, { text: question, type: 'user' }]);
    setQuestion('');
    setIsSubmitting(true);

    try {
      // If no PDF is uploaded, we'll simulate a friendly chat response
      if (!pdfUploaded) {
        setTimeout(() => {
          setMessages((prev) => [
            ...prev, 
            { 
              text: "You haven't uploaded a pdf yet please upload a pdf first, Thank You", 
              type: 'bot' 
            }
          ]);
          setIsSubmitting(false);
        }, 700);
        return;
      }

      // Otherwise, process the PDF-related question
      const response = await axios.post('http://localhost:5000/ask', { question });
      setMessages((prev) => [...prev, { text: response.data.answer, type: 'bot' }]);
    } catch (error) {
      toast.error(error.response?.data?.error || 'Error fetching answer.');
      setMessages((prev) => [...prev, { text: 'Error fetching answer.', type: 'bot' }]);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!file.name.endsWith('.pdf')) {
      toast.error('Please upload a valid PDF file.');
      return;
    }

    const formData = new FormData();
    formData.append('pdf_file', file);
    setIsUploading(true);

    try {
      const response = await axios.post('http://localhost:5000/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          console.log(`Upload progress: ${percentCompleted}%`);
        }
      });
      toast.success('File uploaded successfully!');
      setPdfUploaded(true);
      setUploadedFile(file.name);
    } catch (error) {
      toast.error('File upload failed. Please try again.');
      console.error('Upload error:', error);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="mt-auto relative">
      <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-lg flex items-center p-4 pl-6">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Message Gyansetu..."
          disabled={isSubmitting || isUploading}
          className="flex-1 border-none outline-none text-xl"
        />
        <div className="flex items-center">
          <button 
            type="button" 
            onClick={() => fileInputRef.current.click()}
            disabled={isUploading || isSubmitting}
            className="px-5 py-3 text-gray-700 hover:bg-gray-100 rounded-lg flex items-center text-lg disabled:opacity-50"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
            </svg>
            Attach File
          </button>
          <button
            type="submit"
            disabled={isSubmitting || isUploading}
            className="ml-3 bg-black text-white rounded-full p-4 hover:bg-gray-800 disabled:opacity-50"
          >
            {isSubmitting ? (
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-t-transparent border-white"></div>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
              </svg>
            )}
          </button>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          id="pdf-upload"
          accept=".pdf"
          onChange={handleUpload}
          className="hidden"
        />
      </form>
    </div>
  );
};

export default ChatInput;