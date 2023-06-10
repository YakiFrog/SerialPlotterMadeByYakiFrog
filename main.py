import customtkinter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
import serial
import time
import threading # スレッド用（非同期処理用）
import sys 
import os
import re
import serial.tools.list_ports
import numpy as np

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class MainFrame(customtkinter.CTkFrame):
    def __init__ (self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        
        pdx = 20
        pdy = 10
        
        self.font = ("Arial", 12, "bold")
        self.ser = serial.Serial()
        if self.ser.is_open:
            self.ser.close()
        
        # ここにウィジェットを追加していく
        # ラベルを作成
        self.label = customtkinter.CTkLabel(self, text="Serial Plotter Made By YakiFrog", font=("Arial", 20, "bold"))
        self.label.grid(row=0, column=0, columnspan=2, rowspan=1, padx=pdx, pady=10, sticky="nsew")
        
        # ラベルを作成
        self.label_port = customtkinter.CTkLabel(self, text="Select Serial Port", font=self.font)
        self.label_port.grid(row=1, column=0, columnspan=1, rowspan=1, padx=(pdx, 0), pady=5, sticky="w")
        
        # ポート選択用のコンボボックスを作成
        self.combo_port = customtkinter.CTkComboBox(self, state="readonly", font=self.font, values=["%s" % (p.device) for p in serial.tools.list_ports.comports()])
        self.combo_port.grid(row=1, column=1, columnspan=1, rowspan=1, padx=(0, pdx), pady=5, sticky="ew")
        self.combo_port.set("%s" % (serial.tools.list_ports.comports()[-1].device))
        
        # ラベルを作成
        self.label_baudrate = customtkinter.CTkLabel(self, text="Select Baudrate", font=self.font)
        self.label_baudrate.grid(row=2, column=0, columnspan=1, rowspan=1, padx=(pdx, 0), pady=5, sticky="w")
        
        # ボーレート選択用のコンボボックスを作成
        self.combo_baudrate = customtkinter.CTkComboBox(self, values=["9600", "115200"], state="readonly", font=self.font)
        self.combo_baudrate.grid(row=2, column=1, columnspan=1, rowspan=1, padx=(0, pdx), pady=5, sticky="ew")
        self.combo_baudrate.set("115200")
        
        # Connect
        self.button_connect = customtkinter.CTkButton(self, text="Connect", fg_color="green", command=self.connect, font=self.font)
        self.button_connect.grid(row=3, column=0, columnspan=2, rowspan=1, padx=(pdx, pdx), pady=5, sticky="nsew")
        
        # Disconnect
        self.button_disconnect = customtkinter.CTkButton(self, text="Disconnect", fg_color="#FF3535", command=self.disconnect, font=self.font)
        self.button_disconnect.grid(row=4, column=0, columnspan=2, rowspan=1, padx=(pdx, pdx), pady=5, sticky="nsew")
        
        # Serial Monitor
        self.label_monitor = customtkinter.CTkLabel(self, text="Serial Monitor", font=("Arial", 16, "bold"))
        self.label_monitor.grid(row=5, column=0, columnspan=2, rowspan=1, padx=(pdx, pdx), pady=5, sticky="sw")
        
        # テキストボックスを作成
        self.text_console = customtkinter.CTkTextbox(self, font=("Arial", 12), state="disabled", bg_color="black")
        self.text_console.grid(row=6, column=0, columnspan=2, rowspan=1, padx=(pdx, pdx), pady=5, sticky="nsew")
        # 常に最下部にスクロール
        self.text_console.see("end")
        
        # Entry
        self.entry = customtkinter.CTkEntry(self, font=("Arial", 12))
        self.entry.grid(row=7, column=0, columnspan=2, rowspan=1, padx=(pdx, pdx), pady=5, sticky="nsew")
        
        # Send
        self.button_send = customtkinter.CTkButton(self, text="Send", fg_color="green", command=self.send, font=self.font)
        self.button_send.grid(row=8, column=0, columnspan=2, rowspan=1, padx=(pdx, pdx), pady=5, sticky="nsew")
        
        self.button_disconnect.configure(state="disabled")
        self.button_send.configure(state="disabled")
        
    def connect(self):
        if self.ser.is_open:
            self.ser.close()
        self.ser.port = self.combo_port.get()
        self.ser.baudrate = int(self.combo_baudrate.get())
        self.ser.open()
        self.button_connect.configure(state="disabled")
        self.button_disconnect.configure(state="active")
        self.button_send.configure(state="active")
        
        # スレッドを作成
        self.thread = threading.Thread(target=self.read_serial) # 受信用のスレッドを作成
        # SubFrameのグラフを更新するスレッドを作成 
        self.thread_graph = threading.Thread(target=self.master.frame_graph.update_graph)
        
        # スレッドをデーモン化(とは，メインスレッドが終了したら，サブスレッドも終了するということ)
        self.thread.daemon = False
        self.thread_graph.daemon = False
        # スレッドを起動
        self.thread.start()
        self.thread_graph.start()
        
    def disconnect(self):
        self.button_connect.configure(state="active")
        self.button_disconnect.configure(state="disabled")
        self.button_send.configure(state="disabled")
        self.ser.close()
        
    def send(self):
        self.master.send(self.entry.get())
        
    def read_serial(self):
        while True:
            try: 
                if self.ser.in_waiting: # データが来ている場合
                    # シリアルデータを1行取得
                    line = self.ser.readline().decode("utf-8").strip()
                    # テキストボックスに追加
                    self.text_console.configure(state="normal")
                    self.text_console.insert("end", line + "\n")
                    self.text_console.configure(state="disabled")
                    # 最大行数を超えていたら先頭行を削除
                    if self.text_console.index("end-1c").split(".")[0] == str(100):
                        self.text_console.configure(state="normal")
                        self.text_console.delete("1.0", "2.0")
                        self.text_console.configure(state="disabled")
                    # 常に最下部にスクロール
                    self.text_console.see("end")
                    
                    try:
                        values = np.array(line.split(",")).astype(np.float32).reshape(1,3) # 1行をカンマ区切りで配列に変換
                        self.master.frame_graph.data = np.vstack((self.master.frame_graph.data, values))
                                 
                    except ValueError:
                        print("ValueError")
                        pass
            except:
                pass
      
        
class SubFrame(customtkinter.CTkFrame):
    def __init__ (self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        # ここにウィジェットを追加していく   
        self.data = np.zeros((0,3))
        self.max_points = 200
        self.num_graph = 1
        # Graph ２行2列
        self.fig, self.axes = plt.subplots(ncols=self.num_graph, nrows=1,figsize=(5, 4), dpi=50, tight_layout=True)
        if self.num_graph == 1:
            self.axes = [self.axes]
        for i in range(self.num_graph):
            self.axes[i].set_xlabel("Index")
            self.axes[i].set_ylabel("Value")
            self.axes[i].relim()
            self.axes[i].autoscale_view()
            self.axes[i].legend()
            self.axes[i].grid()
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.canvas.draw()
        
    def update_graph(self):
        while True:
            try:
                if len(self.data) > self.max_points:
                    self.data = self.data[-self.max_points:]
                for i in range(self.num_graph):
                    self.axes[i].cla()
                for i in range(self.data.shape[1]):
                    if i < self.num_graph: # グラフの数よりデータの次元数が少ない場合
                        self.axes[i].plot(self.data[:,i], label="data{}".format(i))
                    else:
                        self.axes[-1].plot(self.data[:,i], label="data{}".format(i))
                for i in range(self.num_graph):
                    self.axes[i].set_xlabel("Index")
                    self.axes[i].set_ylabel("Value")
                    self.axes[i].relim()
                    self.axes[i].autoscale_view()
                    self.axes[i].legend()
                    self.axes[i].grid()
                self.canvas.draw()
                time.sleep(0.02)
            except:
                pass
        

class SerialPlotterGUI(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        threading.Thread.__init__(self) # スレッドグループを作成 (スレッドの管理ができる)
        self.title("Serial Plotter Made By YakiFrog")
        # ウィンドウのサイズ自動
        self.geometry("1000x600")
        # ウィンドウのサイズ変更可
        self.resizable(width=True, height=True)
        # ウィンドウサイズ限界
        self.maxsize(width=2000, height=600) 
        self.minsize(width=350 + 10, height=550)
        # ウィンドウを閉じるボタンを無効化
        self.protocol("WM_DELETE_WINDOW", self.quit) # 終了ボタンが押された時の処理
        
        self.data = np.array([])
        # フレームを作成
        self.frame = MainFrame(self)
        self.frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.frame.grid_rowconfigure((5), weight=1) 
        self.frame.grid_columnconfigure((0, 1), weight=1)
        
        # フレームを作成
        self.frame_graph = SubFrame(self)
        self.frame_graph.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.frame_graph.columnconfigure(0, weight=1)
        self.frame_graph.rowconfigure(0, weight=1)
        
        # フレーム自体の拡大(できるところを選択)
        self.columnconfigure((1), weight=1)   # 0列目と1列目を拡大
        self.rowconfigure(0, weight=1)         # 0行目を拡大
        
if __name__ == '__main__':
    app = SerialPlotterGUI()
    app.mainloop()