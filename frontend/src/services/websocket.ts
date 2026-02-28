import { io, Socket } from "socket.io-client";

class WebSocketService {
  private socket: Socket | null = null;

  connect(teacherId: string, token: string) {
    this.socket = io("ws://localhost:8000", {
      query: { teacher_id: teacherId },
      auth: { token },
    });

    this.socket.on("connect", () => {
      console.log("WebSocket connected");
    });

    return this.socket;
  }

  onEscalation(callback: (data: unknown) => void) {
    this.socket?.on("new_escalation", callback);
  }

  disconnect() {
    this.socket?.disconnect();
  }
}

export const wsService = new WebSocketService();
