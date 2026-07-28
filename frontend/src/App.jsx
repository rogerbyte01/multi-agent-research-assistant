import React, { useState, useEffect, useRef, useCallback } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const Markdown = ({ content }) => {
  if (!content) return null;

  const getHtml = () => {
    let html = content
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    // Code blocks
    html = html.replace(/```([\s\S]*?)```/g, '<pre class="bg-[#0f1423] p-4 rounded-xl overflow-x-auto my-4 border border-white/10 text-[13px] text-gray-300 shadow-inner font-mono"><code>$1</code></pre>');
    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code class="bg-indigo-900/40 text-indigo-300 px-1.5 py-0.5 rounded-md text-[13px] font-mono border border-indigo-500/20">$1</code>');
    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3 class="text-xl font-semibold mt-6 mb-3 text-white">$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2 class="text-2xl font-bold mt-8 mb-4 text-white border-b border-white/10 pb-2">$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1 class="text-3xl font-bold mt-8 mb-4 text-white border-b border-white/10 pb-2">$1</h1>');
    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>');
    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-indigo-400 hover:text-indigo-300 underline underline-offset-2 transition-colors" target="_blank" rel="noopener noreferrer">$1</a>');
    // Lists
    html = html.replace(/^\s*-\s+(.*$)/gim, '<li class="ml-6 list-disc mb-1">$1</li>');
    html = html.replace(/^\s*\*\s+(.*$)/gim, '<li class="ml-6 list-disc mb-1">$1</li>');
    html = html.replace(/^\s*(\d+)\.\s+(.*$)/gim, '<li class="ml-6 list-decimal mb-1">$2</li>');
    // HR
    html = html.replace(/^---/gim, '<hr class="border-white/10 my-8" />');
    // Paragraphs / Line breaks
    html = html.replace(/\n\n/g, '<div class="h-4"></div>');
    html = html.replace(/\n(?!(<li|<h|<pre|<hr|<div))/g, '<br/>');

    return { __html: html };
  };

  return <div className="text-gray-300 leading-relaxed text-[15px]" dangerouslySetInnerHTML={getHtml()} />;
};

const Icons = {
  Search: () => <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>,
  Brain: () => <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>,
  Book: () => <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>,
  Pen: () => <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>,
  Check: () => <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
  Copy: () => <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>,
  Download: () => <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>,
  Plus: () => <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>,
  Folder: () => <svg className="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" /></svg>,
};

const StepIcon = ({ name }) => {
  switch (name) {
    case 'Planner': return <Icons.Brain />;
    case 'Researcher': return <Icons.Book />;
    case 'Writer': return <Icons.Pen />;
    case 'Reviewer': return <Icons.Check />;
    default: return <Icons.Brain />;
  }
};

const formatTime = (ms) => {
  const seconds = Math.floor((ms / 1000) % 60);
  const minutes = Math.floor((ms / (1000 * 60)) % 60);
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
};

export default function App() {
  const [topic, setTopic] = useState('');
  const [isResearching, setIsResearching] = useState(false);
  const [activeResearch, setActiveResearch] = useState(null);
  const [history, setHistory] = useState([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [toast, setToast] = useState(null);
  
  const [steps, setSteps] = useState([]);
  const [finalReport, setFinalReport] = useState(null);
  const [totalTime, setTotalTime] = useState(0);
  const [startTime, setStartTime] = useState(null);
  const [currentTick, setCurrentTick] = useState(Date.now());
  const reportRef = useRef(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  useEffect(() => {
    let interval;
    if (isResearching && startTime) {
      interval = setInterval(() => setCurrentTick(Date.now()), 1000);
    }
    return () => clearInterval(interval);
  }, [isResearching, startTime]);

  const fetchHistory = async () => {
    try {
      setIsLoadingHistory(true);
      const res = await fetch(`${API_BASE}/memory`);
      if (res.ok) {
        const data = await res.json();
        setHistory(data.topics || data || []);
      }
    } catch (err) {
      console.error('Failed to fetch history:', err);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const showToast = (msg, type = 'error') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const startResearch = async (searchTopic) => {
    if (!searchTopic.trim()) return;
    
    setIsResearching(true);
    setActiveResearch(searchTopic);
    setTopic(searchTopic);
    setSteps([]);
    setFinalReport(null);
    setStartTime(Date.now());
    setTotalTime(0);

    try {
      const response = await fetch(`${API_BASE}/research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: searchTopic }),
      });

      if (!response.body) throw new Error("ReadableStream not supported");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          // Flush remaining decoder buffer
          buffer += decoder.decode();
          break;
        }
        
        buffer += decoder.decode(value, { stream: true });
        // Handle both \n\n and \r\n\r\n delimiters
        let lines = buffer.split(/\r?\n\r?\n/);
        buffer = lines.pop() || ''; // keep the last incomplete chunk

        for (let block of lines) {
          if (!block.trim()) continue;
          
          let eventType = 'message';
          let dataStr = '';
          
          block.split(/\r?\n/).forEach(line => {
            if (line.startsWith('event:')) eventType = line.substring(6).trim();
            else if (line.startsWith('data:')) dataStr += (dataStr ? '\n' : '') + line.substring(5).trim();
          });

          // Skip keepalive pings
          if (eventType === 'ping') continue;

          if (dataStr) {
            try {
              const data = JSON.parse(dataStr);
              handleSSEEvent(eventType, data);
            } catch (e) {
              console.error('JSON Parse Error', e);
            }
          }
        }
      }
      // Ensure state is reset even if stream ends without complete event
      setIsResearching(false);
    } catch (error) {
      console.error("Research failed", error);
      showToast('Research connection failed. Please try again.');
      setIsResearching(false);
    }
  };

  const handleSSEEvent = (event, data) => {
    if (event === 'error') {
      showToast(data.message || 'An error occurred');
      setIsResearching(false);
      return;
    }

    if (event === 'complete') {
      setFinalReport(data.report);
      setIsResearching(false);
      setTotalTime(Date.now() - startTime);
      fetchHistory();
      
      setTimeout(() => {
        reportRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 500);
      return;
    }

    if (['Planner', 'Researcher', 'Writer', 'Reviewer'].includes(event)) {
      setSteps(prev => {
        const newSteps = [...prev];
        
        // Find if this specific step is already running or if we need to add a new revision
        // To handle loops, if a step is transitioning from running -> done, update it.
        // If it's a new 'running' event for a step that was already done, it's a new loop iteration.
        
        let existingIdx = newSteps.length - 1;
        while (existingIdx >= 0) {
          if (newSteps[existingIdx].name === event) break;
          existingIdx--;
        }

        if (existingIdx >= 0 && newSteps[existingIdx].status === 'running') {
          // Update existing running step
          newSteps[existingIdx] = {
            ...newSteps[existingIdx],
            status: data.status,
            output: data.output || newSteps[existingIdx].output,
            endTime: data.status === 'done' ? Date.now() : null
          };
        } else {
          // Add new step
          newSteps.push({
            id: Date.now().toString() + Math.random(),
            name: event,
            status: data.status,
            output: data.output,
            startTime: Date.now(),
            endTime: data.status === 'done' ? Date.now() : null
          });
        }
        
        return newSteps;
      });
    }
  };

  const handleCopy = () => {
    if (finalReport) {
      navigator.clipboard.writeText(finalReport);
      showToast('Copied to clipboard!', 'success');
    }
  };

  const handleDownload = () => {
    if (finalReport) {
      const blob = new Blob([finalReport], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Research_Report_${activeResearch.replace(/\s+/g, '_')}.md`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const loadPastResearch = (pastTopic) => {
    // In a real app we might fetch the report by ID. 
    // Here we'll just set it to active and maybe start researching it again or show its cached report if available.
    // Assuming backend /memory returns { topic, report } for now.
    setTopic(pastTopic.topic);
    setActiveResearch(pastTopic.topic);
    if (pastTopic.report) {
      setFinalReport(pastTopic.report);
      setSteps([]);
      setIsResearching(false);
    } else {
      startResearch(pastTopic.topic);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden selection:bg-indigo-500/30">
      
      {/* Toast */}
      {toast && (
        <div className={`fixed top-6 right-6 z-50 px-6 py-3 rounded-lg shadow-lg border transition-all duration-300 animate-float ${
          toast.type === 'error' ? 'bg-red-500/10 border-red-500/50 text-red-200' : 'bg-green-500/10 border-green-500/50 text-green-200'
        }`}>
          {toast.msg}
        </div>
      )}

      {/* Sidebar */}
      <aside className="w-80 glass flex flex-col z-10 shrink-0">
        <div className="p-6 pb-4">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Icons.Brain className="text-white animate-pulse" />
            </div>
            <div>
              <h1 className="font-bold text-lg leading-tight tracking-tight text-white">Synthesia</h1>
              <p className="text-xs text-indigo-400 font-medium">AI Research Agent</p>
            </div>
          </div>

          <button 
            onClick={() => { setFinalReport(null); setSteps([]); setActiveResearch(null); setTopic(''); }}
            className="w-full py-2.5 px-4 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm font-medium text-white transition-all flex items-center justify-center shadow-sm"
          >
            <Icons.Plus /> New Research
          </button>
        </div>

        <div className="px-6 py-2">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">Past Research</h2>
        </div>
        
        <div className="flex-1 overflow-y-auto px-4 pb-6 space-y-2">
          {isLoadingHistory ? (
            Array(5).fill(0).map((_, i) => (
              <div key={i} className="h-16 rounded-lg animate-skeleton" />
            ))
          ) : history.length === 0 ? (
            <p className="text-sm text-gray-500 text-center mt-4">No history yet.</p>
          ) : (
            history.map((h, i) => (
              <button
                key={i}
                onClick={() => loadPastResearch(h)}
                className={`w-full text-left p-3 rounded-xl border transition-all ${
                  activeResearch === h.topic 
                  ? 'bg-indigo-500/10 border-indigo-500/30' 
                  : 'bg-white/5 border-transparent hover:bg-white/10'
                }`}
              >
                <div className="flex items-start gap-3">
                  <Icons.Folder />
                  <div>
                    <h3 className="text-sm font-medium text-gray-200 line-clamp-1">{h.topic}</h3>
                    <p className="text-xs text-gray-500 mt-1">{(h.sub_questions || []).length} sub-questions</p>
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative overflow-hidden bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-900/20 via-[#0a0e1a] to-[#0a0e1a]">
        
        {!activeResearch && !finalReport && !isResearching ? (
          <div className="flex-1 flex flex-col items-center justify-center p-8 z-10 animate-fade-in">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500/20 to-indigo-600/20 border border-indigo-500/30 flex items-center justify-center mb-8 animate-float">
              <Icons.Brain className="w-10 h-10 text-indigo-400" />
            </div>
            <h2 className="text-4xl font-bold mb-4 text-white tracking-tight">What shall we explore today?</h2>
            <p className="text-gray-400 mb-10 max-w-lg text-center text-lg">
              Enter a topic and watch the multi-agent system plan, research, write, and review a comprehensive report.
            </p>
            
            <div className="w-full max-w-2xl relative gradient-border-focus rounded-full">
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && startResearch(topic)}
                placeholder="e.g. The impact of quantum computing on cryptography..."
                className="w-full bg-[#111827] text-white border border-gray-700/50 rounded-full py-4 pl-6 pr-16 focus:outline-none placeholder-gray-500 shadow-xl"
              />
              <button 
                onClick={() => startResearch(topic)}
                className="absolute right-2 top-2 bottom-2 aspect-square bg-indigo-500 hover:bg-indigo-600 rounded-full flex items-center justify-center transition-colors shadow-lg"
              >
                <Icons.Search />
              </button>
            </div>

            <div className="mt-12 flex flex-wrap gap-3 justify-center max-w-2xl">
              {['AGI Timelines', 'CRISPR in Agriculture', 'Solid State Batteries'].map(suggestion => (
                <button
                  key={suggestion}
                  onClick={() => { setTopic(suggestion); startResearch(suggestion); }}
                  className="px-4 py-2 rounded-full bg-white/5 border border-white/10 text-sm text-gray-300 hover:bg-white/10 hover:text-white transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto p-8 lg:p-12 scroll-smooth">
            <div className="max-w-4xl mx-auto space-y-12">
              
              {/* Active Search Header */}
              <div className="flex flex-col gap-2">
                <span className="text-xs font-semibold tracking-wider text-indigo-400 uppercase">Research Topic</span>
                <h2 className="text-3xl font-bold text-white">{activeResearch}</h2>
              </div>

              {/* Agent Trace Timeline */}
              {steps.length > 0 && (
                <div className="bg-[#111827]/50 rounded-2xl border border-white/10 p-6 shadow-2xl backdrop-blur-sm">
                  <h3 className="text-sm font-semibold text-gray-300 mb-6 flex justify-between items-center">
                    <span>Agent Trace</span>
                    {totalTime > 0 && (
                      <span className="text-indigo-400 font-mono bg-indigo-500/10 px-3 py-1 rounded-full">
                        Total time: {formatTime(totalTime)}
                      </span>
                    )}
                  </h3>
                  
                  <div className="space-y-6 relative before:absolute before:inset-0 before:ml-6 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-indigo-500/50 before:to-transparent">
                    {steps.map((step, idx) => {
                      const isRunning = step.status === 'running';
                      const duration = isRunning 
                        ? currentTick - step.startTime 
                        : (step.endTime - step.startTime);
                        
                      return (
                        <div key={step.id} className="relative flex items-start gap-4">
                          <div className={`relative z-10 w-12 h-12 rounded-full border-2 flex items-center justify-center shrink-0 bg-[#0a0e1a] transition-colors
                            ${isRunning ? 'border-indigo-500 text-indigo-400 animate-pulse-glow' : 'border-gray-700 text-gray-500'}
                            ${step.status === 'done' ? 'border-green-500/50 text-green-400' : ''}
                          `}>
                            <StepIcon name={step.name} />
                            {isRunning && (
                              <div className="absolute top-0 right-0 w-3 h-3 bg-indigo-500 rounded-full border-2 border-[#0a0e1a]"></div>
                            )}
                          </div>
                          
                          <div className="flex-1 bg-white/5 rounded-xl border border-white/5 p-4 hover:bg-white/[0.07] transition-colors">
                            <div className="flex justify-between items-center mb-2">
                              <h4 className="font-semibold text-white">{step.name}</h4>
                              <div className="flex items-center gap-3">
                                <span className="font-mono text-xs text-gray-400">{formatTime(Math.max(0, duration))}</span>
                                <span className={`text-xs px-2.5 py-1 rounded-full font-medium
                                  ${isRunning ? 'bg-indigo-500/20 text-indigo-300' : 'bg-green-500/20 text-green-300'}
                                `}>
                                  {step.status}
                                </span>
                              </div>
                            </div>
                            
                            {step.output && (
                              <div className="mt-3 pt-3 border-t border-white/5">
                                <p className="text-sm text-gray-400 line-clamp-2 italic">
                                  {typeof step.output === 'object' ? JSON.stringify(step.output).substring(0, 100) + '...' : step.output}
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Final Report */}
              {finalReport && (
                <div className="bg-[#111827] rounded-2xl border border-white/10 shadow-2xl overflow-hidden" ref={reportRef}>
                  <div className="bg-white/5 border-b border-white/10 px-8 py-5 flex items-center justify-between">
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                      <Icons.Book /> Research Report
                    </h3>
                    <div className="flex gap-3">
                      <button 
                        onClick={handleCopy}
                        className="flex items-center text-sm font-medium text-gray-300 bg-white/5 hover:bg-white/10 px-4 py-2 rounded-lg border border-white/10 transition-colors"
                      >
                        <Icons.Copy /> Copy
                      </button>
                      <button 
                        onClick={handleDownload}
                        className="flex items-center text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-500 px-4 py-2 rounded-lg transition-colors shadow-lg shadow-indigo-500/20"
                      >
                        <Icons.Download /> Download
                      </button>
                    </div>
                  </div>
                  <div className="p-8 lg:p-12">
                    <Markdown content={finalReport} />
                  </div>
                </div>
              )}

              {/* Loader padding */}
              {isResearching && (
                <div className="py-12 flex justify-center">
                  <div className="flex items-center gap-3 text-indigo-400 font-medium">
                    <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                    Synthesizing knowledge...
                  </div>
                </div>
              )}

            </div>
          </div>
        )}
      </main>
    </div>
  );
}
