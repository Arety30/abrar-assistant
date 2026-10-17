import React, { useEffect, useRef } from 'react';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';

const AIOSDashboard = () => {
  const terminalRef = useRef(null);
  const xterm = useRef(null);

  useEffect(() => {
    xterm.current = new Terminal({
      cursorBlink: true,
      theme: { background: '#1e1e1e' }
    });
    const fitAddon = new FitAddon();
    xterm.current.loadAddon(fitAddon);
    xterm.current.open(terminalRef.current);
    fitAddon.fit();

    xterm.current.writeln('Welcome to Abrar AI OS v1.0');
    xterm.current.prompt = () => {
      xterm.current.write('\r\n$ ');
    };
    xterm.current.prompt();

    let command = '';
    xterm.current.onData(async (e) => {
      if (e === '\r') {
        xterm.current.writeln('');
        // Send command to backend
        try {
          const response = await fetch('/api/controller', {
            method: 'POST',
            body: JSON.stringify({ command }),
            headers: { 'Content-Type': 'application/json' },
          });
          const data = await response.json();
          xterm.current.writeln(data.message);
        } catch (err) {
          xterm.current.writeln('Error connecting to AI Kernel.');
        }
        command = '';
        xterm.current.prompt();
      } else if (e === '\u007f') { // Backspace
        if (command.length > 0) {
          command = command.slice(0, -1);
          xterm.current.write('\b \b');
        }
      } else {
        command += e;
        xterm.current.write(e);
      }
    });

    return () => xterm.current.dispose();
  }, []);

  return (
    <div style={{ height: '100vh', width: '100vw', backgroundColor: '#000' }}>
      <div ref={terminalRef} style={{ height: '100%', width: '100%' }} />
    </div>
  );
};

export default AIOSDashboard;
