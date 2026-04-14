import React, { useState, useEffect, useRef } from 'react';

function App() {
  // ✅ 修复：三种类型齐全！
  const [contentType, setContentType] = useState('blog');
  const [messages, setMessages] = useState([
    { id: 1, role: 'assistant', content: '你好。请上传PDF/DOCX文档 → 选择类型 → 点击生成。' }
  ]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  
  const [showFullResult, setShowFullResult] = useState(false);
  const [currentFullContent, setCurrentFullContent] = useState('');
  const scrollRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) setSelectedFile(file);
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
      content: `请求生成：${
        contentType === 'blog' ? '博客文章' :
        contentType === 'case_study' ? '案例分析' :
        '视频脚本'
      }`
    }]);
    
    const formData = new FormData();
    formData.append('content_type', contentType);
    formData.append('file', selectedFile);

    try {
      const res = await fetch('http://localhost:8000/generate_from_file', {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
        },
        body: formData,
        mode: 'cors',
      });

      const data = await res.json();
      if (res.ok) {
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          role: 'assistant',
          content: '✅ 内容生成成功！',
          isResult: true,
          fullContent: JSON.stringify(data.data, null, 2),
        }]);
      } else {
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          role: 'assistant',
          content: `错误：${data.detail}`,
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
              {/* ✅ 三种按钮齐全 */}
              <button
                onClick={() => setContentType('blog')}
                className={`w-full text-left px-4 py-3 rounded-lg text-sm transition-all ${contentType === 'blog' ? 'bg-blue-600 text-white shadow-md' : 'text-gray-600 bg-gray-50'}`}
              >
                博客文章
              </button>
              <button
                onClick={() => setContentType('case_study')}
                className={`w-full text-left px-4 py-3 rounded-lg text-sm transition-all ${contentType === 'case_study' ? 'bg-blue-600 text-white shadow-md' : 'text-gray-600 bg-gray-50'}`}
              >
                案例分析
              </button>
              <button
                onClick={() => setContentType('video')}
                className={`w-full text-left px-4 py-3 rounded-lg text-sm transition-all ${contentType === 'video' ? 'bg-blue-600 text-white shadow-md' : 'text-gray-600 bg-gray-50'}`}
              >
                视频脚本
              </button>
            </div>
          </section>

          <section>
            <label className="text-xs font-bold text-gray-500 uppercase tracking-widest block mb-4">核心资料库</label>
            <input
              type="file"
              ref={fileInputRef}
              className="hidden"
              onChange={handleFileChange}
              accept=".pdf,.docx"
            />
            <div
              onClick={() => fileInputRef.current.click()}
              className={`border border-gray-200 rounded-xl p-6 text-center cursor-pointer min-h-[160px] ${selectedFile ? 'bg-green-50 border-green-200' : 'hover:bg-gray-50'}`}
            >
              {selectedFile ? (
                <div className="text-xs text-green-700">
                  <p>已选择：</p>
                  <p className="font-mono">{selectedFile.name}</p>
                </div>
              ) : (
                <p className="text-xs text-gray-400">点击上传 PDF / DOCX 文件</p>
              )}
            </div>
            <button
              onClick={handleGenerate}
              disabled={!selectedFile || isGenerating}
              className="w-full mt-6 py-4 rounded-xl text-sm font-bold bg-blue-600 text-white disabled:bg-gray-200"
            >
              {isGenerating ? '生成中...' : '🚀 生成内容'}
            </button>
          </section>
        </div>
      </div>

      <div className="flex-1 p-10 overflow-y-auto" ref={scrollRef}>
        {messages.map(msg => (
          <div key={msg.id} className={`mb-4 flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] p-5 rounded-2xl ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-white'}`}>
              {msg.content}
              {msg.isResult && (
                <button
                  onClick={() => {
                    setCurrentFullContent(msg.fullContent);
                    setShowFullResult(true);
                  }}
                  className="mt-3 text-sm text-blue-600 underline block"
                >
                  查看结果
                </button>
              )}
            </div>
          </div>
        ))}
        {isGenerating && (
          <div className="bg-white p-4 rounded-2xl text-sm text-gray-400">生成中...</div>
        )}
      </div>

{showFullResult && (
  <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4">
    <div className="bg-white rounded-xl w-full max-w-3xl max-h-[85vh] overflow-y-auto p-6">
      {(() => {
        try {
          // 1. 万能解析：不管你套了多少层 JSON，我都给你扒干净
          let res = currentFullContent;
          if (typeof res === "string") res = JSON.parse(res);
          if (typeof res === "string") res = JSON.parse(res); // 双重嵌套也能解

          // 2. 如果是 { title, content } 结构
          if (res?.title && res?.content) {
            return (
              <div className="space-y-4 text-gray-800">
                <h2 className="text-xl font-bold text-blue-600">{res.title}</h2>
                <div className="text-base leading-relaxed whitespace-pre-line">
                  {res.content}
                </div>
              </div>
            );
          }

          // 3. 兜底：直接显示干净文本
          return <pre className="text-sm whitespace-pre-wrap">{JSON.stringify(res, null, 2)}</pre>;
        } catch (e) {
          // 4. 解析失败就直接原文展示
          return <div className="whitespace-pre-line">{currentFullContent}</div>;
        }
      })()}

      <button
        onClick={() => setShowFullResult(false)}
        className="mt-6 px-4 py-2 bg-blue-600 text-white rounded"
      >
        关闭
      </button>
    </div>
  </div>
)}
    </div>
  );
}

export default App;