import React, { useState, useRef, useEffect } from 'react';
import { Send, Image as ImageIcon, Loader2, Bot, User } from 'lucide-react';

interface Message {
    role: 'user' | 'agent';
    content: string;
    image?: string;
    generatedImage?: string;
    timestamp: Date;
}

interface ChatInterfaceProps {
    onStateUpdate: (newState: any) => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onStateUpdate }) => {
    const [messages, setMessages] = useState<Message[]>([
        {
            role: 'agent',
            content: 'Hello! I am your Smart Christmas Tree assistant. How can I help you customize your tree today? 🎄',
            timestamp: new Date()
        }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [selectedImage, setSelectedImage] = useState<File | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setSelectedImage(e.target.files[0]);
        }
    };

    const formatTime = (date: Date) => {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if ((!input.trim() && !selectedImage) || isLoading) return;

        const userMessage: Message = {
            role: 'user',
            content: input,
            image: selectedImage ? URL.createObjectURL(selectedImage) : undefined,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const formData = new FormData();
            formData.append('message', input || (selectedImage ? "I uploaded an image." : ""));
            if (selectedImage) {
                formData.append('file', selectedImage);
            }

            const response = await fetch('http://localhost:8001/api/chat', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) throw new Error('Failed to send message');

            const data = await response.json();

            setMessages(prev => [...prev, {
                role: 'agent',
                content: data.response,
                generatedImage: data.generated_image,
                timestamp: new Date()
            }]);

            if (data.tree_state) {
                onStateUpdate(data.tree_state);
            }

        } catch (error) {
            console.error('Error:', error);
            setMessages(prev => [...prev, {
                role: 'agent',
                content: 'Sorry, I encountered an error processing your request. Please try again.',
                timestamp: new Date()
            }]);
        } finally {
            setIsLoading(false);
            setSelectedImage(null);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    return (
        <div className="flex flex-col h-full bg-gray-950 border-l border-white/5 text-white font-sans">
            <div className="p-6 border-b border-white/5 bg-gray-900/50 backdrop-blur-md">
                <h2 className="text-xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                    Tree Designer
                </h2>
                <p className="text-xs text-gray-400 mt-1">AI-Powered Customization</p>
            </div>

            <div className="flex-1 min-h-0 overflow-y-auto p-6 space-y-10">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`flex items-start gap-12 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                        {/* Avatar */}
                        <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${msg.role === 'agent' ? 'bg-emerald-900/50 text-emerald-400' : 'bg-indigo-900/50 text-indigo-400'
                            }`}>
                            {msg.role === 'agent' ? <Bot size={20} /> : <User size={20} />}
                        </div>

                        {/* Message Content */}
                        <div className={`flex flex-col max-w-[70%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                            <div className={`rounded-2xl px-6 py-4 shadow-sm ${msg.role === 'user'
                                ? 'bg-indigo-600 text-white rounded-tr-none'
                                : 'bg-gray-800 text-gray-100 rounded-tl-none border border-white/5'
                                }`}>
                                {msg.image && (
                                    <img src={msg.image} alt="User upload" className="w-full h-48 object-cover rounded-lg mb-3" />
                                )}
                                {msg.generatedImage && (
                                    <img src={msg.generatedImage} alt="Agent generated" className="w-full h-auto object-contain rounded-lg mb-3 border border-white/10" />
                                )}
                                <p className="whitespace-pre-wrap leading-relaxed text-[15px]">{msg.content}</p>
                            </div>
                            <span className="text-xs text-gray-500 mt-2 px-1">
                                {formatTime(msg.timestamp)}
                            </span>
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="flex items-start gap-12">
                        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-emerald-900/50 text-emerald-400 flex items-center justify-center">
                            <Bot size={20} />
                        </div>
                        <div className="bg-gray-800 rounded-2xl rounded-tl-none px-6 py-4 border border-white/5 flex items-center gap-3">
                            <Loader2 className="w-4 h-4 animate-spin text-emerald-400" />
                            <span className="text-sm text-gray-400">Thinking...</span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="px-6 pt-6 pb-20 bg-gray-900/30">
                <form onSubmit={handleSubmit} className="relative flex items-end gap-2 p-2 rounded-[2rem] border border-white/10 bg-gray-800/80 shadow-2xl focus-within:border-indigo-500/50 transition-colors">
                    {selectedImage && (
                        <div className="absolute bottom-full mb-4 left-0 flex items-center gap-2 bg-gray-800 border border-white/10 p-2 rounded-xl shadow-xl">
                            <span className="text-xs text-gray-400 truncate max-w-[200px] px-2">{selectedImage.name}</span>
                            <button
                                type="button"
                                onClick={() => {
                                    setSelectedImage(null);
                                    if (fileInputRef.current) fileInputRef.current.value = '';
                                }}
                                className="p-1 hover:bg-white/10 rounded-full text-gray-400 hover:text-white transition-colors"
                            >
                                ×
                            </button>
                        </div>
                    )}

                    <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        className="p-3 text-gray-400 hover:text-indigo-400 hover:bg-white/5 rounded-full transition-all duration-200"
                    >
                        <ImageIcon className="w-5 h-5" />
                    </button>
                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleImageSelect}
                        accept="image/*"
                        className="hidden"
                    />
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Type a message..."
                        style={{ color: '#ffffff' }}
                        className="flex-1 bg-transparent border-none text-white caret-white placeholder-gray-400 focus:outline-none px-2 py-3"
                    />
                    <button
                        type="submit"
                        disabled={isLoading || (!input.trim() && !selectedImage)}
                        className="p-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-full transition-all duration-200 shadow-lg hover:shadow-indigo-500/25"
                    >
                        <Send className="w-4 h-4" />
                    </button>
                </form>
            </div>
        </div>
    );
};

export default ChatInterface;
