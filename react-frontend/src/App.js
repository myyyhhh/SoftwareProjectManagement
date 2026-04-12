import React, { useState, useEffect, useRef } from 'react';

function App() {
  const [contentType, setContentType] = useState('blog');
  const [brandTags, setBrandTags] = useState(['专业', '科技感']);
  const [newTagInput, setNewTagInput] = useState('');
  const [messages, setMessages] = useState([
    { id: 1, role: 'assistant', content: '你好。请在左侧上传参考文档并设置品牌调性，我将为您生成一致性内容。' }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(null);
  
  // 用于预览完整内容的弹窗状态
  const [showFullResult, setShowFullResult] = useState(false);
  const [currentFullContent, setCurrentFullContent] = useState('');

  const scrollRef = useRef(null);
  const fileInputRef = useRef(null);

  // 自动滚动聊天区域
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, isGenerating]);

  // 处理文件上传
  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setUploadingFile(file.name);
      setIsGenerating(true);
      setTimeout(() => {
        setMessages(prev => [...prev, {
          id: Date.now(),
          role: 'assistant',
          content: `文件加载成功：${file.name}。知识库解析完毕，您可以开始生成任务。`
        }]);
        setIsGenerating(false);
      }, 1500);
    }
  };

  const removeTag = (tag) => setBrandTags(brandTags.filter(t => t !== tag));
  const addTag = (e) => {
    if (e.key === 'Enter' && newTagInput.trim()) {
      if (!brandTags.includes(newTagInput.trim())) setBrandTags([...brandTags, newTagInput.trim()]);
      setNewTagInput('');
    }
  };

  const handleSend = (e) => {
    if (e) e.preventDefault();
    if (!uploadingFile) { alert('请先上传资料'); return; }
    
    const typeMap = { blog: '博客文章', case: '案例研究', script: '视频脚本' };
    const taskName = inputValue.trim() || `生成${typeMap[contentType]}`;
    
    setMessages(prev => [...prev, { id: Date.now(), role: 'user', content: taskName }]);
    setIsGenerating(true);
    setInputValue('');

    // 模拟 AI 生成过程
    setTimeout(() => {
      const simulatedFullContent = `【完整生成内容展示】\n\n标题：基于《${uploadingFile}》的${typeMap[contentType]}\n\n正文：\n我们在分析产品核心逻辑时，重点参考了您提供的原始文档。按照“${brandTags.join('、')}”的品牌调性要求，我们对语言风格进行了深度对齐。\n\n1. 核心观点对齐：确保了所有专业术语与《${uploadingFile}》保持高度一致。\n2. 风格润色：不仅消除了表达歧义，还通过 AI 算法强化了“${brandTags[0]}”的感知度。\n\n结论：该内容已通过品牌一致性校验，可直接发布。`;

      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: `内容生成完毕。已严格遵循以下品牌调性：${brandTags.join('、')}。`,
        isResult: true,
        resultPreview: `摘要：本文档基于上传的产品资料进行了深度解析，确保所有专业术语及表达逻辑符合品牌一致性规范...`,
        fullContent: simulatedFullContent // 将完整内容存入该条消息中
      }]);
      setIsGenerating(false);
    }, 1500);
  };

  return (
    <div className="flex h-screen bg-gray-100 overflow-hidden font-sans text-gray-800">
      {/* 左侧配置栏 - 宽度 400px */}
      <div className="w-[400px] bg-white border-r flex flex-col shadow-sm z-10">
        <div className="p-8">
          <h1 className="text-3xl font-bold text-blue-600 tracking-tight">内容智能体</h1>
          <p className="text-xs text-gray-400 mt-2 uppercase tracking-widest">Brand Consistency Agent</p>
        </div>

        <div className="flex-1 px-10 space-y-10 overflow-y-auto pt-4">
          <section>
            <label className="text-xs font-bold text-gray-500 uppercase tracking-widest block mb-4">核心资料库</label>
            <input type="file" ref={fileInputRef} className="hidden" onChange={handleFileUpload} accept=".pdf,.doc,.docx" />
            <div 
              onClick={() => fileInputRef.current.click()}
              className={`border border-gray-200 rounded-xl p-6 text-center cursor-pointer transition flex flex-col justify-center items-center min-h-[160px] ${uploadingFile ? 'bg-green-50 border-green-200 shadow-inner' : 'hover:bg-gray-50 bg-gray-50/30'}`}
            >
              {uploadingFile ? (
                <div className="text-xs text-green-600 leading-relaxed">
                  <p className="font-bold text-green-700 mb-2">已加载参考：</p>
                  <p className="break-all px-2 font-mono">{uploadingFile}</p>
                </div>
              ) : (
                <p className="text-xs text-gray-400 leading-loose">点击此处<br/>上传品牌说明文档</p>
              )}
            </div>
          </section>

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

          <section className="pb-8">
            <label className="text-xs font-bold text-gray-500 uppercase tracking-widest block mb-4">品牌风格标签</label>
            <div className="flex flex-wrap gap-2 mb-4">
              {brandTags.map(tag => (
                <span key={tag} className="flex items-center bg-white border border-gray-200 text-gray-600 text-[10px] px-3 py-1.5 rounded-full shadow-sm">
                  {tag}
                  <button onClick={() => removeTag(tag)} className="ml-2 font-bold hover:text-red-500">×</button>
                </span>
              ))}
            </div>
            <input type="text" value={newTagInput} onChange={(e) => setNewTagInput(e.target.value)} onKeyDown={addTag}
              placeholder="添加标签..." className="w-full p-3 bg-gray-50 border border-gray-200 rounded-lg text-xs focus:outline-none focus:border-blue-400 focus:bg-white" />
          </section>
        </div>
      </div>

      {/* 右侧对话区 */}
      <div className="flex-1 flex flex-col bg-gray-50/50">
        <div className="flex-1 overflow-y-auto p-10 space-y-8" ref={scrollRef}>
          {messages.map(msg => (
            <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] p-5 rounded-2xl ${msg.role === 'user' ? 'bg-blue-600 text-white shadow-lg' : 'bg-white border border-gray-100 shadow-sm'}`}>
                <div className="text-sm leading-relaxed">{msg.content}</div>
                {msg.isResult && (
                  <div className="mt-5 pt-5 border-t border-gray-100">
                    <div className="text-[11px] text-gray-400 bg-gray-50 p-4 rounded-xl mb-4 font-mono break-all italic leading-relaxed">
                      {msg.resultPreview}
                    </div>
                    <div className="flex justify-between items-center text-[10px] font-bold">
                      <span className="text-green-600 border border-green-200 px-2 py-1 rounded">一致性校验通过</span>
                      <button 
                        onClick={() => {
                          setCurrentFullContent(msg.fullContent);
                          setShowFullResult(true);
                        }}
                        className="text-blue-600 hover:text-blue-800 underline underline-offset-4"
                      >
                        查看生成结果
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
          {isGenerating && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-100 px-6 py-4 rounded-2xl text-xs text-gray-400 italic shadow-sm flex items-center animate-pulse">
                系统正在进行品牌一致性校验...
              </div>
            </div>
          )}
        </div>

        {/* 底部输入区 */}
        <div className="p-10 bg-white border-t border-gray-100">
          <form onSubmit={handleSend} className="max-w-4xl mx-auto relative">
            <input type="text" value={inputValue} onChange={(e) => setInputValue(e.target.value)}
              placeholder={uploadingFile ? "请输入详细的任务描述指令..." : "请先在左侧上传品牌资料"}
              disabled={!uploadingFile}
              className="w-full p-5 pr-24 bg-gray-50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-1 focus:ring-blue-500 focus:bg-white text-sm disabled:opacity-50"
            />
            <button type="submit" disabled={!uploadingFile || isGenerating} className="absolute right-3 top-2.5 bg-blue-600 text-white px-6 py-2.5 rounded-xl text-xs font-bold hover:bg-blue-700 shadow-lg shadow-blue-200 disabled:shadow-none">
              发送指令
            </button>
          </form>
        </div>
      </div>

      {/* 完整内容预览弹窗 (Modal) */}
      {showFullResult && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-6 backdrop-blur-sm">
          <div className="bg-white w-full max-w-4xl max-h-[85vh] rounded-3xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in duration-200">
            <div className="p-6 border-b flex justify-between items-center bg-gray-50/50">
              <h2 className="text-lg font-bold text-gray-700">生成结果预览</h2>
              <button onClick={() => setShowFullResult(false)} className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-gray-200 text-gray-500 transition-colors text-2xl">×</button>
            </div>
            <div className="flex-1 overflow-y-auto p-10">
              <div className="whitespace-pre-wrap text-gray-700 leading-loose text-base font-serif">
                {currentFullContent}
              </div>
            </div>
            <div className="p-6 border-t bg-gray-50/50 text-right">
              <button onClick={() => setShowFullResult(false)} className="bg-blue-600 text-white px-8 py-2.5 rounded-xl text-sm font-bold hover:bg-blue-700 transition-shadow shadow-md">
                关闭预览
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;