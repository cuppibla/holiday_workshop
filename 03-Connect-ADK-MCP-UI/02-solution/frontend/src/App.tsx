import React, { useState, useEffect } from 'react';
import TreeScene from './components/TreeScene';
import ChatInterface from './components/ChatInterface';

function App() {
  const [treeState, setTreeState] = useState({
    lights_color: "warm_white",
    ornament_texture: "default_gold",
    theme: "emerald_gold"
  });

  // Fetch initial state
  useEffect(() => {
    fetch('http://localhost:8001/api/state')
      .then(res => res.json())
      .then(data => setTreeState(data))
      .catch(err => console.error("Failed to fetch initial state:", err));
  }, []);

  return (
    <div className="flex w-screen h-screen overflow-hidden bg-black">
      {/* 3D Scene Container - Takes up full space but chat overlays on right */}
      <div className="flex-1 relative">
        <TreeScene treeState={treeState} />

        {/* Overlay Title */}
        <div className="absolute top-8 left-8 pointer-events-none">
          <h1 className="text-4xl font-light text-white tracking-widest uppercase opacity-80">
            Smart Christmas
          </h1>
          <p className="text-emerald-400 tracking-wider text-sm mt-2">
            AI-Powered Customization
          </p>
        </div>
      </div>

      {/* Chat Interface - Fixed width sidebar */}
      <div className="w-[400px] h-full relative z-10 shadow-2xl">
        <ChatInterface onStateUpdate={setTreeState} />
      </div>
    </div>
  );
}

export default App;
