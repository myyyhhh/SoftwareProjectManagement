
import React, { useState, useEffect, useRef } from 'react';

function App() {
  const [contentType, setContentType] = useState('blog');
  const [messages, setMessages] = useState([
    { id: 1, role: 'assistant', content: '你好。请选择类型 → 上传文档 → 点击生成。' }
  ]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null); // 保存真实文件对象
  
  const [showFullResult, setShowFullResult] = useState(false);
  const [currentFullContent, setCurrentFullContent] = useState('');

  const scrollRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  // 选择文件
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setMessages(prev => [...prev, {
        id: Date.now(),
        role: 'assistant',
        content: `已上传：${file.name}`
      }]);
    }
  };


  const handleGenerate = async () => {
    if (!selectedFile) {
      alert('请先上传文件');
      return;
    }

    setIsGenerating(true);
    setMessages(prev => [...prev, {
      id: Date.now(),
      role: 'user',
      content: `开始生成：${contentType === 'blog' ? '博客文章' : contentType === 'case' ? '案例研究' : '视频脚本'}`
    }]);

    // 构造 FormData
    const formData = new FormData();
    formData.append('content_type', contentType);
    formData.append('file', selectedFile);

    try {
      const res = await fetch('http://localhost:8000/generate_from_file', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();

      if (res.ok) {
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          role: 'assistant',
          content: '内容生成成功！',
          isResult: true,
          fullContent: data.content || '无返回内容',
        }]);
      } else {
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          role: 'assistant',
          content: `错误：${data.detail || '生成失败'}`,
          isError: true
        }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: '请求失败，请检查后端服务是否启动',
        isError: true
      }]);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-100 overflow-hidden font-sans text-gray-800">
      <div className="w-[400px] bg-white border-r flex flex-col shadow-sm z-10">
        <div className="p-8">
          <h1 className="text-3xl font-bold text-blue-600 tracking-tight">内容智能体</h1>
          <p className="text-xs text-gray-400 mt-2 uppercase tracking-widest">Brand Consistency Agent</p>
        </div>

        <div className="flex-1 px-10 space-y-16 overflow-y-auto pt-4">
          <section>
            <label className="text-xs font-bold text-gray-500 uppercase tracking-widest block mb-4">任务类型</label>
            <div className="space-y-2">
              {['blog', 'case', 'script'].map(type => (
                <button key={type} onClick={() => setContentType(type)}
                  className={`w-full text-left px-4 py-3 rounded-lg text-sm transition-all ${contentType === type ? 'bg-blue-600 text-white shadow-md' : 'text-gray-600 bg-gray-50 border border-transparent hover:border-gray-200'}`}>
                  {type === 'blog' ? '博客文章' : type === 'case' ? '案例研究' : '视频脚本'}
                </button>
              ))}
            </div>
          </section>

          <section>
            <label className="text-xs font-bold text-gray-500 uppercase tracking-widest block mb-4">核心资料库</label>
            <input type="file" ref={fileInputRef} className="hidden" onChange={handleFileChange} accept=".pdf,.doc,.docx" />
            <div 
              onClick={() => fileInputRef.current.click()}
              className={`border border-gray-200 rounded-xl p-6 text-center cursor-pointer transition flex flex-col justify-center items-center min-h-[160px] ${selectedFile ? 'bg-green-50 border-green-200 shadow-inner' : 'hover:bg-gray-50 bg-gray-50/30'}`}
            >
              {selectedFile ? (
                <div className="text-xs text-green-600 leading-relaxed">
                  <p className="font-bold text-green-700 mb-2">已选择文件：</p>
                  <p className="break-all px-2 font-mono">{selectedFile.name}</p>
                </div>
              ) : (
                <p className="text-xs text-gray-400 leading-loose">点击此处<br/>上传品牌说明文档</p>
              )}
            </div>

            <button
              onClick={handleGenerate}
              disabled={!selectedFile || isGenerating}
              className={`w-full mt-6 py-4 rounded-xl text-sm font-bold transition-all ${
                selectedFile && !isGenerating 
                  ? 'bg-blue-600 text-white shadow-md hover:bg-blue-700' 
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
            >
              {isGenerating ? '生成中...' : '生成内容'}
            </button>
          </section>
        </div>
      </div>

      <div className="flex-1 flex flex-col bg-gray-50/50">
        <div className="flex-1 overflow-y-auto p-10 space-y-8" ref={scrollRef}>
          {messages.map(msg => (
            <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] p-5 rounded-2xl 
                ${msg.role === 'user' ? 'bg-blue-600 text-white shadow-lg' : ''}
                ${msg.role === 'assistant' && !msg.isError ? 'bg-white border border-gray-100 shadow-sm' : ''}
                ${msg.isError ? 'bg-red-50 border border-red-200 text-red-600 shadow-sm' : ''}`}
              >
                <div className="text-sm leading-relaxed">{msg.content}</div>
                {msg.isResult && (
                  <div className="mt-3">
                    <button 
                      onClick={() => {
                        setCurrentFullContent(msg.fullContent);
                        setShowFullResult(true);
                      }}
                      className="text-blue-600 text-sm underline"
                    >
                      查看生成结果
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
          {isGenerating && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-100 px-6 py-4 rounded-2xl text-xs text-gray-400 italic shadow-sm flex items-center animate-pulse">
                系统正在生成内容...
              </div>
            </div>
          )}
        </div>
      </div>

      {showFullResult && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-6 backdrop-blur-sm">
          <div className="bg-white w-full max-w-4xl max-h-[85vh] rounded-3xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in duration-200">
            <div className="p-6 border-b flex justify-between items-center bg-gray-50/50">
              <h2 className="text-lg font-bold text-gray-700">生成结果预览</h2>
              <button onClick={() => setShowFullResult(false)} className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-gray-200 text-gray-500 transition-colors text-2xl">×</button>
            </div>
            <div className="flex-1 overflow-y-auto p-10">
              <pre className="whitespace-pre-wrap text-gray-700 leading-loose text-base">{currentFullContent}</pre>
            </div>
            <div className="p-6 border-t bg-gray-50/50 text-right">
              <button onClick={() => setShowFullResult(false)} className="bg-blue-600 text-white px-8 py-2.5 rounded-xl text-sm font-bold hover:bg-blue-700 transition-shadow shadow-md">关闭预览</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;