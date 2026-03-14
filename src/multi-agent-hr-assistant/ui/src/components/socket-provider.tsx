"use client";

import { createContext, useContext, useEffect, useRef, useState } from "react";
import { io, Socket } from "socket.io-client";

type SocketContextType = {
  socket: Socket | null;
  isConnected: boolean;
};

const SocketContext = createContext<SocketContextType>({
  socket: null,
  isConnected: false,
});

export const useSocket = () => {
  return useContext(SocketContext);
};

export const SocketProvider = ({ children }: { children: React.ReactNode }) => {
  const socketRef = useRef<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [socket, setSocket] = useState<Socket | null>(null);

  useEffect(() => {
    if (!socketRef.current) {
      socketRef.current = io(
        process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
        {
          path: "/socket.io",
          addTrailingSlash: false,
          autoConnect: true,
        },
      );
      
      setSocket(socketRef.current);
    }

    const sock = socketRef.current;

    const onConnect = () => setIsConnected(true);
    const onDisconnect = () => setIsConnected(false);

    sock.on("connect", onConnect);
    sock.on("disconnect", onDisconnect);

    if (sock.connected) setIsConnected(true);

    return () => {
      sock.off("connect", onConnect);
      sock.off("disconnect", onDisconnect);
      
    };
  }, []);

 
  useEffect(() => {
    return () => {
      socketRef.current?.disconnect();
      socketRef.current = null;
      setSocket(null);
    };
  }, []);

  return (
    <SocketContext.Provider value={{ socket, isConnected }}>
      {children}
    </SocketContext.Provider>
  );
};