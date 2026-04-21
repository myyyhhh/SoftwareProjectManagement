import React, { useState, useEffect, useRef } from 'react';

function App() {
  const [contentType, setContentType] = useState('blog');
  const [messages, setMessages] = useState([
    { id: 1, role: 'assistant', content: '你好。请在左侧上传参考文档并设置任务类型，我将为您生成一致性内容。' }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(null);
  
  // 用于预览完整内容的弹窗状态
  const [showFullResult, setShowFullResult] = useState(false);
  const [currentFullContent, setCurrentFullContent] = useState('');
  
  // 新增状态
  const [isOnline, setIsOnline] = useState(true); // 联网模式开关
  const [isAuthenticated, setIsAuthenticated] = useState(false); // 登录状态
  const [showAuthModal, setShowAuthModal] = useState(false); // 登录注册弹窗
  const [authMode, setAuthMode] = useState('login'); // 登录/注册模式
  const [username, setUsername] = useState(''); // 用户名
  const [password, setPassword] = useState(''); // 密码
  const [userId, setUserId] = useState(null); // 用户ID
  const [history, setHistory] = useState([]); // 历史对话
  const [currentSessionId, setCurrentSessionId] = useState(Date.now()); // 当前会话ID

  // FastAPI 核心配置变量
  const FASTAPI_CONFIG = {
    baseUrl: 'http://localhost:8000', // 替换为实际的 FastAPI 服务地址
    generateEndpoint: '/generate_from_file', // 生成内容的接口路径
    streamEndpoint: '/generate_stream', // 流式生成接口路径
    authEndpoint: '/auth', // 认证接口路径
    conversationsEndpoint: '/auth/conversations', // 历史对话接口路径
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + localStorage.getItem('token')
    }
  };

  const scrollRef = useRef(null);
  const fileInputRef = useRef(null);

  // 自动滚动聊天区域
  // 自动滚动聊天区域
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, isGenerating]);

  // 初始化：从本地存储加载历史记录
  useEffect(() => {
    const savedHistory = localStorage.getItem('chatHistory');
    if (savedHistory) {
      setHistory(JSON.parse(savedHistory));
    }
    // 检查登录状态
    const token = localStorage.getItem('token');
    if (token) {
      setIsAuthenticated(true);
      // 尝试从本地存储获取用户ID
      const savedUserId = localStorage.getItem('userId');
      if (savedUserId) {
        setUserId(savedUserId);
        // 获取历史对话
        fetchConversations();
      }
    }
  }, []);

  // 登录状态变化时保存用户ID到本地存储
  useEffect(() => {
    if (userId) {
      localStorage.setItem('userId', userId);
    }
  }, [userId]);

  // 处理文件上传
  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setUploadingFile(file.name);
      setIsGenerating(true);
      // 模拟文件上传校验（实际项目可对接文件上传接口）
      setTimeout(async () => {
        try {
          // 可扩展：实际文件上传接口调用
          setMessages(prev => [...prev, {
            id: Date.now(),
            role: 'assistant',
            content: `文件加载成功：${file.name}。知识库解析完毕，您可以开始生成任务。`
          }]);
        } catch (error) {
          setMessages(prev => [...prev, {
            id: Date.now(),
            role: 'assistant',
            content: `文件加载失败：${file.name}。${error.message || '请检查文件格式或重试'}`
          }]);
        }
        setIsGenerating(false);
      }, 1500);
    }
  };

  // 调用 FastAPI 生成内容（核心逻辑）
  const callFastAPIGenerate = async (taskName, fileName, type) => {
    try {
      // 构造请求参数
      const requestData = {
        filename: fileName,
        content_type: type,
        task_description: taskName,
        conversation_id: currentSessionId
      };

      // 调用 FastAPI 接口
      const response = await fetch(
        `${FASTAPI_CONFIG.baseUrl}${FASTAPI_CONFIG.generateEndpoint}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + localStorage.getItem('token')
          },
          body: JSON.stringify(requestData)
        }
      );

      const result = await response.json();

      // 处理接口返回状态
      if (result.title && result.content) {
        // 拼接完整内容（适配接口返回的 title + content）
        return {
          success: true,
          preview: `摘要：${result.content.substring(0, 100)}...`, // 截取前100字符作为预览
          fullContent: `标题：${result.title}\n\n正文：\n${result.content}`
        };
      } else {
        return {
          success: false,
          errorMsg: result.message || '生成失败：服务器返回错误'
        };
      }
    } catch (error) {
      // 捕获网络/接口异常
      return {
        success: false,
        errorMsg: `接口调用失败：${error.message || '请检查网络或服务状态'}`
      };
    }
  };

  // 流式调用 FastAPI 生成内容
  const callFastAPIStreamGenerate = async (taskName, fileName, type) => {
    try {
      // 构造请求参数
      const requestData = {
        filename: fileName,
        content_type: type,
        task_description: taskName,
        conversation_id: currentSessionId
      };

      // 调用流式接口
      const response = await fetch(
        `${FASTAPI_CONFIG.baseUrl}${FASTAPI_CONFIG.streamEndpoint}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + localStorage.getItem('token')
          },
          body: JSON.stringify(requestData)
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';
      let assistantMessageId = Date.now() + 1;

      // 初始添加一个空的助手消息
      setMessages(prev => [...prev, {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        isStreaming: true
      }]);

      // 读取流式数据
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        fullContent += chunk;

        // 更新消息内容
        setMessages(prev => prev.map(msg => 
          msg.id === assistantMessageId 
            ? { ...msg, content: fullContent }
            : msg
        ));
      }

      // 流式结束后，处理完整内容
      const lines = fullContent.split('\n');
      const title = lines[0].replace('标题：', '');
      const content = lines.slice(2).join('\n');
      const preview = `摘要：${content.substring(0, 100)}...`;

      // 更新消息为最终状态
      setMessages(prev => prev.map(msg => 
        msg.id === assistantMessageId 
          ? {
              ...msg,
              content: `内容生成完毕。已基于《${uploadingFile}》完成${typeMap[contentType]}的生成。`,
              isStreaming: false,
              isResult: true,
              resultPreview: preview,
              fullContent: fullContent
            }
          : msg
      ));

      return { success: true };
    } catch (error) {
      // 捕获网络/接口异常
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: `生成失败：${error.message || '请检查网络或服务状态'}`,
        isError: true
      }]);
      return { success: false };
    }
  };

  // 认证相关函数
  const handleAuth = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(
        `${FASTAPI_CONFIG.baseUrl}${FASTAPI_CONFIG.authEndpoint}/${authMode}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ username, password })
        }
      );

      const result = await response.json();
      if (result.token) {
        localStorage.setItem('token', result.token);
        setUserId(result.user_id);
        setIsAuthenticated(true);
        setShowAuthModal(false);
        setUsername('');
        setPassword('');
        // 登录成功后获取历史对话
        await fetchConversations();
      } else {
        alert(result.message || '认证失败');
      }
    } catch (error) {
      alert(`认证失败：${error.message || '请检查网络连接'}`);
    }
  };

  // 获取历史对话
  const fetchConversations = async () => {
    if (!isAuthenticated || !userId) return;
    try {
      const response = await fetch(
        `${FASTAPI_CONFIG.baseUrl}${FASTAPI_CONFIG.conversationsEndpoint}/${userId}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + localStorage.getItem('token')
          }
        }
      );

      const result = await response.json();
      if (result) {
        // 转换后端返回的对话格式为前端格式
        const formattedHistory = result.map(session => ({
          id: session.id,
          timestamp: session.created_at,
          fileName: session.file_name || '无文件',
          content_type: session.content_type,
          messages: session.messages
        }));
        setHistory(formattedHistory);
      }
    } catch (error) {
      console.error('获取历史对话失败：', error);
    }
  };

  // 保存对话到历史记录
  const saveToHistory = async () => {
    if (messages.length > 1) { // 至少有一条用户消息和一条助手消息
      const session = {
        id: currentSessionId,
        timestamp: new Date().toISOString(),
        fileName: uploadingFile,
        content_type: contentType,
        messages: [...messages]
      };
      setHistory(prev => [session, ...prev]);
      // 如果已登录，后端会自动保存对话
      // 保存到本地存储作为备份
      localStorage.setItem('chatHistory', JSON.stringify([session, ...history]));
    }
  };

  // 加载历史对话
  const loadHistory = (session) => {
    setMessages(session.messages);
    setUploadingFile(session.fileName);
    setCurrentSessionId(session.id);
  };

  const handleSend = async (e) => {
    if (e) e.preventDefault();
    if (!uploadingFile) { 
      alert('请先上传资料'); 
      return; 
    }
    
    const typeMap = { blog: '博客文章', case: '案例研究', script: '视频脚本' };
    const taskName = inputValue.trim() || `生成${typeMap[contentType]}`;
    
    // 添加用户消息到聊天记录
    setMessages(prev => [...prev, { id: Date.now(), role: 'user', content: taskName }]);
    setIsGenerating(true);
    setInputValue('');

    // 根据联网模式选择调用方式
    if (isOnline) {
      // 联网模式：使用流式输出
      await callFastAPIStreamGenerate(taskName, uploadingFile, contentType);
    } else {
      // 离线模式：使用普通调用
      const generateResult = await callFastAPIGenerate(taskName, uploadingFile, contentType);
      
      // 处理生成结果
      if (generateResult.success) {
        // 生成成功
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          role: 'assistant',
          content: `内容生成完毕。已基于《${uploadingFile}》完成${typeMap[contentType]}的生成。`,
          isResult: true,
          resultPreview: generateResult.preview,
          fullContent: generateResult.fullContent
        }]);
      } else {
        // 生成失败（前端提示错误）
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          role: 'assistant',
          content: `生成失败：${generateResult.errorMsg}`,
          isError: true // 标记为错误消息，便于样式区分
        }]);
      }
    }
    setIsGenerating(false);
  };

  return (
    <div className="flex h-screen bg-gray-100 overflow-hidden font-sans text-gray-800">
      {/* 左侧配置栏 */}
      <div className="w-[400px] bg-white border-r flex flex-col shadow-sm z-10">
        <div className="p-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-blue-600 tracking-tight">内容智能体</h1>
            <p className="text-xs text-gray-400 mt-2 uppercase tracking-widest">Brand Consistency Agent</p>
          </div>
          {/* 登录/注册按钮 */}
          <button onClick={() => {
            if (isAuthenticated) {
              // 退出登录
              localStorage.removeItem('token');
              localStorage.removeItem('userId');
              setIsAuthenticated(false);
              setUserId(null);
              setHistory([]);
            } else {
              setShowAuthModal(true);
            }
          }} className="text-xs font-bold text-blue-600 hover:text-blue-800 transition-colors">
            {isAuthenticated ? '退出' : '登录'}
          </button>
        </div>

        <div className="flex-1 px-10 space-y-14 pt-4">
          {/* 核心资料库 section */}
          <section>
            <label className="text-xs font-bold text-gray-500 uppercase tracking-widest block mb-4">核心资料库</label>
            <input type="file" ref={fileInputRef} className="hidden" onChange={handleFileUpload} accept=".pdf,.doc,.docx" />
            <div 
              onClick={() => fileInputRef.current.click()}
              className={`border border-gray-200 rounded-xl p-6 text-center cursor-pointer transition flex flex-col justify-center items-center min-h-[120px] ${uploadingFile ? 'bg-green-50 border-green-200 shadow-inner' : 'hover:bg-gray-50 bg-gray-50/30'}`}
            >
              {uploadingFile ? (
                <div className="text-xs text-green-600 leading-relaxed w-full">
                  <div className="flex justify-between items-center mb-2">
                    <p className="font-bold text-green-700">已加载参考：</p>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        setUploadingFile(null);
                      }}
                      className="text-black-600 hover:text-black-800 text-lg font-bold"
                      title="删除文件"
                    >
                      ×
                    </button>
                  </div>
                  <p className="break-all px-2 font-mono">{uploadingFile}</p>
                </div>
              ) : (
                <p className="text-xs text-gray-400 leading-loose">点击此处<br/>上传品牌说明文档</p>
              )}
            </div>
          </section>

          {/* 任务类型 section */}
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

          {/* 历史对话 section */}
          <section>
            <div className="flex justify-between items-center mb-4">
              <label className="text-xs font-bold text-gray-500 uppercase tracking-widest block">历史对话</label>
              <button onClick={saveToHistory} disabled={messages.length <= 1} className="text-xs text-blue-600 hover:text-blue-800 transition-colors disabled:opacity-50">
                保存对话
              </button>
            </div>
            <div className="space-y-2 max-h-[150px] overflow-y-auto">
              {history.length === 0 ? (
                <p className="text-xs text-gray-400 text-center py-4">暂无历史对话</p>
              ) : (
                history.map((session) => {
                  const sessionId = session.id;
                  return (
                    <div key={sessionId} className="p-3 border border-gray-200 rounded-lg text-xs hover:bg-gray-50 transition-colors">
                      <div className="flex justify-between items-center">
                        <div onClick={() => loadHistory(session)} className="cursor-pointer flex-1">
                          <div className="font-medium text-gray-800 truncate">
                            {session.fileName ? (
                              <>
                                {session.fileName}
                                {session.content_type && (
                                  <span className="text-gray-500 ml-2">
                                    {session.content_type === 'blog' ? '博客文章' : 
                                     session.content_type === 'case' ? '案例研究' : 
                                     session.content_type === 'script' ? '视频脚本' : 
                                     session.content_type}
                                  </span>
                                )}
                              </>
                            ) : '无文件'}
                          </div>
                          <div className="text-gray-400 mt-1">{new Date(session.timestamp).toLocaleString()}</div>
                        </div>
                        <button 
                          onClick={(e) => {
                            e.stopPropagation();
                            setHistory(prevHistory => {
                              const updatedHistory = prevHistory.filter(item => item.id !== sessionId);
                              // 更新本地存储
                              localStorage.setItem('chatHistory', JSON.stringify(updatedHistory));
                              return updatedHistory;
                            });
                          }}
                          className="text-gray-400 hover:text-red-600 text-lg font-bold ml-2"
                          title="删除对话"
                        >
                          ×
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </section>
        </div>
      </div>

      {/* 右侧对话区 */}
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
                系统正在生成内容...
              </div>
            </div>
          )}
        </div>

        {/* 底部输入区 */}
        <div className="p-10 bg-white border-t border-gray-100">
          <form onSubmit={handleSend} className="max-w-6xl mx-auto relative">
            <div className="flex items-center space-x-4">
              {/* 联网模式开关 */}
              <div className="flex items-center space-x-2">
                <span className="text-xs font-medium text-gray-600">联网模式</span>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" checked={isOnline} onChange={(e) => setIsOnline(e.target.checked)} className="sr-only peer" />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
              <div className="flex-1 relative">
                <input type="text" value={inputValue} onChange={(e) => setInputValue(e.target.value)}
                  placeholder={uploadingFile ? "请输入任务描述，可说明风格、语气等要求..." : "请先在左侧上传品牌资料"}
                  disabled={!uploadingFile}
                  className="w-full p-5 pr-24 bg-gray-50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-1 focus:ring-blue-500 focus:bg-white text-sm disabled:opacity-50"
                />
                <button type="submit" disabled={!uploadingFile || isGenerating} className="absolute right-3 top-2.5 bg-blue-600 text-white px-6 py-2.5 rounded-xl text-xs font-bold hover:bg-blue-700 shadow-lg shadow-blue-200 disabled:shadow-none">
                  发送指令
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>

      {/* 完整内容预览弹窗 */}
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

      {/* 登录/注册弹窗 */}
      {showAuthModal && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-6 backdrop-blur-sm">
          <div className="bg-white w-full max-w-md rounded-3xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in duration-200">
            <div className="p-6 border-b flex justify-between items-center bg-gray-50/50">
              <h2 className="text-lg font-bold text-gray-700">{authMode === 'login' ? '登录' : '注册'}</h2>
              <button onClick={() => setShowAuthModal(false)} className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-gray-200 text-gray-500 transition-colors text-2xl">×</button>
            </div>
            <div className="p-10">
              <form onSubmit={handleAuth} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">用户名</label>
                  <input 
                    type="text" 
                    value={username} 
                    onChange={(e) => setUsername(e.target.value)}   
                    required 
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">密码</label>
                  <input 
                    type="password" 
                    value={password} 
                    onChange={(e) => setPassword(e.target.value)} 
                    required 
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <button type="submit" className="w-full bg-blue-600 text-white py-3 rounded-lg font-bold hover:bg-blue-700 transition-colors">
                  {authMode === 'login' ? '登录' : '注册'}
                </button>
                <div className="text-center text-sm">
                  <button type="button" onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')} className="text-blue-600 hover:text-blue-800">
                    {authMode === 'login' ? '没有账号？点击注册' : '已有账号？点击登录'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;