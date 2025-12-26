#!/bin/bash

# 定义会话名称
SESSION="rss-client"

# 1. 检查会话是否存在
tmux has-session -t $SESSION 2>/dev/null

# 如果会话不存在，则创建新会话
if [ $? != 0 ]; then
    # ==========================================
    # 核心修改点：
    # 创建会话时直接指定第一个窗口的名字为 "editor"
    # 这样无论它是窗口 0 还是窗口 1，名字都是对的
    # ==========================================
    tmux new-session -d -s $SESSION -n "editor"

    # 在 editor 窗口（当前窗口）确保进入了项目目录（可选）
    # tmux send-keys -t $SESSION:editor "cd ~/AI-RSS-Hub" C-m

    # ------------------------------------------
    # 创建第二个窗口：名为 "server"
    # 不指定 -t $SESSION:1，而是让 tmux 自动追加
    # ------------------------------------------
    tmux new-window -t $SESSION -n "server"
    # 使用窗口名 "server" 来发送命令，而不是数字
    tmux send-keys -t $SESSION:server "uvicorn main:app --reload" C-m

    # ------------------------------------------
    # 创建第三个窗口：名为 "monitor"
    # ------------------------------------------
    tmux new-window -t $SESSION -n "monitor"
    tmux send-keys -t $SESSION:monitor "htop" C-m

    # ------------------------------------------
    # 最后回到代码编辑窗口
    # 同样使用名字定位，避免数字差异
    # ------------------------------------------
    tmux select-window -t $SESSION:editor
fi

# 2. 智能进入逻辑 (防止嵌套错误)
if [ -n "$TMUX" ]; then
    # 如果已经在 tmux 里面，则切换过去
    echo "Switching to session $SESSION..."
    tmux switch-client -t $SESSION
else
    # 如果在外面，则 attach
    tmux attach -t $SESSION
fi
