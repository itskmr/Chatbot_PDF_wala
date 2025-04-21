import React, { useState, useEffect } from 'react';
import ChatWindow from './components/ChatWindow.jsx';
import ChatInput from './components/ChatInput.jsx';
import Header from './components/Header.jsx';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

function App() {
  const [pdfUploaded, setPdfUploaded] = useState(false);
  const [messages, setMessages] = useState([]);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [showWelcome, setShowWelcome] = useState(true);
  const [conversationStarted, setConversationStarted] = useState(false); // New state to track conversation
  const [statusMessage, setStatusMessage] = useState(
    "No PDF selected. You can ask general questions or select another PDF."
  );

  // Update showWelcome logic to hide welcome section after conversation starts
  useEffect(() => {
    if (messages.length > 0) {
      setConversationStarted(true);
      setShowWelcome(false);
    } else if (pdfUploaded) {
      setShowWelcome(false);
    } else {
      setShowWelcome(true);
      setConversationStarted(false);
    }
  }, [messages, pdfUploaded]);

  const startNewChat = () => {
    setMessages([]);
    setPdfUploaded(false);
    setUploadedFile(null);
    setConversationStarted(false); // Reset conversation state
    setStatusMessage("No PDF selected. You can ask general questions or select another PDF.");
    setShowWelcome(true);
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <ToastContainer position="top-center" autoClose={3000} />
      <Header onNewChat={startNewChat} />
      <main className="flex-1 overflow-hidden flex flex-col w-4/5 mx-auto p-6">
        <div className="flex flex-col h-full">
          {showWelcome && !conversationStarted && (
            <div className="flex flex-col items-center pt-12 pb-10">
              <div className="w-10 h-10 bg-purple-100 rounded-full mb-6 flex items-center justify-center">
                <img
                  src="logo.jpeg"
                  alt="Bot Avatar"
                  className="w-8 h-8"
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.src =
                      "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%236D28D9'%3E%3Cpath d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-4a4 4 0 100-8 4 4 0 000 8z'/%3E%3C/svg%3E";
                  }}
                />
              </div>
              <div className="border-2 border-purple-500 rounded-xl w-full max-w-2xl p-6 text-center">
                <h3 className="text-2xl mb-2 font-medium">How can I help you today?</h3>
                {uploadedFile && (
                  <p className="text-lg text-gray-700">
                    Thanks for uploading {uploadedFile}. You can ask any questions from this PDF, Gyansetu will help you to answer this.
                  </p>
                )}
                {isUploading && (
                  <div className="mt-3 flex justify-center items-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
                    <span className="ml-3 text-purple-600">Uploading your file...</span>
                  </div>
                )}
              </div>
            </div>
          )}
          <ChatWindow
            messages={messages}
            statusMessage={statusMessage}
            showWelcome={showWelcome}
            conversationStarted={conversationStarted} // Pass new prop
          />
          <ChatInput
            setMessages={setMessages}
            pdfUploaded={pdfUploaded}
            setPdfUploaded={setPdfUploaded}
            setUploadedFile={setUploadedFile}
            isUploading={isUploading}
            setIsUploading={setIsUploading}
            setStatusMessage={setStatusMessage}
          />
          <div className="text-center text-base text-gray-500 mt-4 mb-2">
            Powered by Gyansetu.ai
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;