; 设置坐标模式为相对于窗口（这样即使窗口移动了，点击位置也相对准确）
CoordMode, Mouse, Window

; EEG Start
; 运行应用
Run, "./EEG_Upper/eegsdk_demo.exe"
; 等待窗口出现并激活
WinWait, ahk_exe eegsdk_demo.exe
WinActivate, ahk_exe eegsdk_demo.exe
; 强制移动并调整大小
WinMove, ahk_exe eegsdk_demo.exe, , 100, 100, 1200, 1200
; 等待应用加载完成
Sleep, 2000 
; 模拟点击按钮
; Click, 847, 104

; EMG Start
Run, "./EMG_Upper/emgsdk_demo.exe"
WinWait, ahk_exe emgsdk_demo.exe
WinActivate, ahk_exe emgsdk_demo.exe
WinMove, ahk_exe emgsdk_demo.exe, , 100, 200, 1200, 1200
Sleep, 2000 
; 自动最小化
Click, 1000, 27