import React, { useRef, useEffect } from 'react';

const ChatWindow = ({ messages, showWelcome }) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Add emoji to bot responses occasionally
  const getBotResponse = (text) => {
    // Simple example adding emoji - you can expand this
    if (text.toLowerCase().includes('great') || text.toLowerCase().includes('good')) {
      return (
        <>
          {text} <span role="img" aria-label="smile">😊</span>
        </>
      );
    }
    return text;
  };

  return (
    <div className={`flex-1 overflow-y-auto px-6 ${showWelcome ? 'pt-0' : 'pt-8'}`}>
      {messages.map((msg, index) => (
        <div 
          key={index} 
          className={`mb-8 max-w-3/4 ${
            msg.type === 'user' 
              ? 'ml-auto text-right' 
              : ''
          }`}
        >
          {msg.type !== 'user' && (
            <div className="text-base text-red-500 font-medium mb-2">Gyansetu</div>
          )}
          <div className={`inline-block p-4 rounded-xl ${
            msg.type === 'user' 
              ? 'bg-gray-100 text-gray-800 text-xl' 
              : 'bg-white border-2 border-gray-200 text-gray-800 text-xl'
          }`}>
            {msg.type === 'user' ? msg.text : getBotResponse(msg.text)}
          </div>
          {msg.type !== 'user' && (
            <div className="flex mt-3">
              <button className="mr-3 text-gray-500 hover:text-gray-800 text-xl">
                <span role="img" aria-label="copy"> </span>
              </button>
              <button className="text-gray-500 hover:text-gray-800 text-xl">
                <span role="img" aria-label="thumbs down"> </span>
              </button>
            </div>
          )}
        </div>
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default ChatWindow;