import React from 'react';

const Header = ({ onNewChat }) => {
  return (
    <header className="flex justify-between items-center p-6 bg-white border-b border-gray-200">
      <h1 className="text-2xl font-bold">HL City Bot</h1>
      <button 
        onClick={onNewChat}
        className="bg-purple-600 text-white px-6 py-3 rounded-lg flex items-center text-lg font-medium"
      >
        <span className="mr-2 text-xl">New chat</span> +
      </button>
    </header>
  );
};

export default Header;