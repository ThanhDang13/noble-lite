---------------

## Subagents

Spawn subagents to isolate context, parallelize independent work, or offload bulk mechanical tasks. Don't spawn when the parent needs the reasoning, when synthesis requires holding things together, or when spawn overhead dominates.

Pick the cheapest model that can do the subtask well:
- Haiku: bulk mechanical work, no judgment
- Sonnet: scoped research, code exploration, in-scope synthesis
- Opus: subtasks needing real planning or tradeoffs

If a subagent realizes it needs a higher tier than itself, return to the parent.

Parent owns final output and cross-spawn synthesis. User instructions override.

## Preferred Tools

### Data Fetching

1. **WebFetch**: free, text-only, works on public pages that don't block bots.
2. **agent-browser CLI**: free, local Rust CLI + Chrome via CDP. For dynamic pages or auth walls that WebFetch can't handle. Returns the accessibility tree with element refs (@e1, @e2). ~82% fewer tokens than screenshot-based tools. Install: `npm i -g agent-browser && agent-browser install`. Use `snapshot` for AI-friendly DOM state, element refs for interaction.
3. **Notice recurring fetch patterns and propose wrapping them as dedicated tools.** When the same fetch/parse logic comes up more than once, suggest wrapping it as a named tool (e.g. a skill file or a .py script that calls `agent-browser` with the snapshot and extraction steps baked in for that source). Add the entry to `## Dedicated Tools` below and reference it by name on future calls.

### PDF Files

Use 'pdftotext', not the 'Read' tool. Use 'Read' only when the user directly asks to analyze images or charts inside the document. Read loads PDFs as images.

## Dedicated Tools

<!-- List project-specific tools here. For each, link to its skill or script file (e.g. `tools/reddit_fetch.py`). The orchestration logic lives in those files, not here. -->

---------------


# CLAUDE.md — Đồ Án Môn Học: Linux System Programming

## Tổng Quan Dự Án

Đồ án hệ thống Linux gồm 2 yêu cầu chính:

- **YC1**: Lập trình shell, lập trình hệ thống (C), kernel module
- **YC2**: Tối giản Ubuntu, build custom kernel, thay kernel

Mọi việc build/test kernel và module đều thực hiện **trong VM (QEMU/KVM)**, không bao giờ trên host.

---

## Cấu Trúc Thư Mục

```
project/
├── CLAUDE.md                  ← file này
├── scripts/                   ← YC1: Shell scripts
│   ├── backup.sh
│   ├── cleanup.sh
│   ├── scheduler.sh
│   ├── installer.sh
│   └── timectl.sh
├── userspace/                 ← YC1: Lập trình C
│   ├── process-manager/
│   ├── file-manager/
│   ├── socket-server/
│   ├── socket-client/
│   └── network-monitor/
├── kernel/                    ← YC1: Kernel module
│   └── monitor-module/
│       ├── monitor.c
│       ├── Makefile
│       └── README.md
├── kernel-build/              ← YC2: Build custom kernel
├── minimal-ubuntu/            ← YC2: Tối giản Ubuntu
└── docs/
```

---

## Môi Trường

| Thành phần | Vai trò |
|---|---|
| Host (Ubuntu 24) | Viết code, quản lý VM, snapshot |
| Dev VM (4 core / 6GB / 50GB) | Build kernel, compile, test script |
| Test VM (2 core / 2GB / 20GB) | Boot custom kernel, test firewall/network |

**Tuyệt đối không** build kernel, load module, hay replace kernel trên host.

---

## Phase 1 — Shell Scripts (scripts/)

### Mục tiêu
Viết các shell script Bash cho các tác vụ tự động hóa hệ thống.

### Danh sách script cần hoàn thành

| File | Chức năng | Trạng thái |
|---|---|---|
| `backup.sh` | Backup file/thư mục, nén, ghi log | [ ] |
| `cleanup.sh` | Dọn log cũ, temp files, giải phóng disk | [ ] |
| `scheduler.sh` | Thiết lập cron job / systemd timer | [ ] |
| `installer.sh` | Wrapper cài đặt package qua apt/dpkg | [ ] |
| `timectl.sh` | Quản lý timezone, NTP, đồng bộ thời gian | [ ] |

### Yêu cầu kỹ thuật mỗi script
- Có `--help` usage
- Ghi log ra file (ví dụ `/var/log/project/backup.log`)
- Xử lý lỗi với `set -euo pipefail`
- Có thể chạy qua cron không cần tương tác

### Lệnh test
```bash
chmod +x scripts/*.sh
./scripts/backup.sh /home/user /backup/dest
./scripts/cleanup.sh --days 7
./scripts/installer.sh nginx
./scripts/timectl.sh --set-tz Asia/Ho_Chi_Minh --enable-ntp
```

---

## Phase 2 — System Programming C (userspace/)

### Mục tiêu
Lập trình C dùng POSIX API: process, file, socket, network.

### Các chương trình cần hoàn thành

#### 2.1 Process Manager (userspace/process-manager/)
- Dùng: `fork`, `exec`, `wait`, `signal`, `pipe`
- Chức năng:
  - Liệt kê process đang chạy (đọc `/proc`)
  - Detect zombie process
  - Hiển thị process tree
  - Kill process theo PID hoặc tên

```bash
cd userspace/process-manager
make
./process-manager --list
./process-manager --tree
./process-manager --zombies
```

#### 2.2 File Manager (userspace/file-manager/)
- Dùng: `open`, `read`, `write`, `mmap`, `stat`, `inotify`
- Chức năng:
  - Phân tích metadata file
  - Tìm file trùng lặp (so sánh hash)
  - Quét quyền truy cập bất thường
  - Monitor thay đổi thư mục real-time

```bash
cd userspace/file-manager
make
./file-manager --analyze /home
./file-manager --duplicates /data
./file-manager --watch /etc
```

#### 2.3 Socket Server (userspace/socket-server/)
- Dùng: `socket`, `bind`, `listen`, `accept`, `epoll`
- Chức năng:
  - TCP multi-client server dùng `epoll`
  - Hỗ trợ file transfer
  - Chat server cơ bản

```bash
cd userspace/socket-server
make
./socket-server --port 8080 --mode chat
./socket-server --port 9090 --mode file-transfer
```

#### 2.4 Socket Client (userspace/socket-client/)
- Kết nối tới socket-server
- Test gửi/nhận dữ liệu, upload/download file

#### 2.5 Network Monitor (userspace/network-monitor/)
- Đọc `/proc/net/tcp`, `/proc/net/udp`, `/proc/net/dev`
- Chức năng:
  - Mini netstat: hiển thị kết nối đang mở
  - Port monitor: cảnh báo khi port mới mở
  - Connection monitor: thống kê traffic

```bash
cd userspace/network-monitor
make
./network-monitor --connections
./network-monitor --ports
./network-monitor --watch --interval 2
```

### Cấu trúc Makefile mỗi chương trình
```makefile
CC = gcc
CFLAGS = -Wall -Wextra -O2 -g
TARGET = <tên chương trình>

$(TARGET): main.c
	$(CC) $(CFLAGS) -o $@ $^

clean:
	rm -f $(TARGET)
```

---

## Phase 3 — Kernel Module (kernel/monitor-module/)

### Mục tiêu
Viết Linux Kernel Module theo dõi process, expose qua `/proc/process_monitor`.

### File cần tạo

#### kernel/monitor-module/monitor.c
```c
// Cấu trúc tối thiểu cần có:
// - module_init / module_exit
// - Tạo /proc/process_monitor
// - Đọc danh sách process từ task_struct
// - Trả về: PID, tên process, memory usage
// - MODULE_LICENSE("GPL")
```

#### kernel/monitor-module/Makefile
```makefile
obj-m += monitor.o
KDIR := /lib/modules/$(shell uname -r)/build

all:
	make -C $(KDIR) M=$(PWD) modules

clean:
	make -C $(KDIR) M=$(PWD) clean
```

### Workflow build/test module (thực hiện trong Test VM)
```bash
# Build
cd kernel/monitor-module
make

# Load
sudo insmod monitor.ko

# Kiểm tra
dmesg | tail -20
cat /proc/process_monitor

# Unload
sudo rmmod monitor

# Kiểm tra đã remove
lsmod | grep monitor
```

### Output /proc/process_monitor cần hiển thị
```
PID    NAME             VMRSS(kB)
1      systemd          4096
2      kthreadd         0
...
```

### Lưu ý quan trọng
- **Bắt buộc snapshot VM trước khi `insmod`**
- Nếu kernel panic → restore snapshot
- Test trên Test VM, không phải Dev VM khi đang build

---

## Phase 4 — Build Custom Kernel (kernel-build/)

### Workflow (thực hiện trong Dev VM)

```bash
# 1. Tải source
git clone --depth=1 https://github.com/torvalds/linux.git kernel-build/linux-src
cd kernel-build/linux-src

# 2. Copy config hiện tại làm base
cp /boot/config-$(uname -r) .config
make olddefconfig

# 3. Tối giản (tắt những thứ không cần)
make menuconfig
# Tắt: Bluetooth, Sound, Printer, Debug info, Unused drivers
# Bật: ext4, virtio, networking, custom module support

# 4. Build (trong Dev VM)
make -j$(nproc) 2>&1 | tee build.log

# 5. SNAPSHOT TEST VM TRƯỚC KHI TIẾP

# 6. Install (trong Test VM)
sudo make modules_install
sudo make install
sudo update-grub

# 7. Reboot Test VM
sudo reboot

# 8. Kiểm tra
uname -r
```

### Cấu hình tối giản đề xuất (menuconfig)
```
# Tắt
CONFIG_BT=n              # Bluetooth
CONFIG_SOUND=n           # Sound
CONFIG_USB_PRINTER=n     # Printer
CONFIG_DEBUG_INFO=n      # Debug symbols (giảm size)

# Bật
CONFIG_EXT4_FS=y
CONFIG_VIRTIO=y
CONFIG_VIRTIO_NET=y
CONFIG_VIRTIO_BLK=y
CONFIG_NET=y
```

---

## Phase 5 — Minimal Ubuntu (minimal-ubuntu/)

### Workflow

```bash
# 1. Cài debootstrap (trên Dev VM)
sudo apt install debootstrap

# 2. Build rootfs tối giản
sudo debootstrap noble minimal-ubuntu/rootfs http://archive.ubuntu.com/ubuntu

# 3. Chroot vào và cấu hình
sudo chroot minimal-ubuntu/rootfs /bin/bash
apt install --no-install-recommends \
  systemd \
  openssh-server \
  iproute2 \
  bash \
  apt
exit

# 4. Tạo service tự khởi động
# Tạo file: minimal-ubuntu/rootfs/etc/systemd/system/process-monitor.service
```

### File service (minimal-ubuntu/rootfs/etc/systemd/system/process-monitor.service)
```ini
[Unit]
Description=Process Monitor
After=network.target

[Service]
ExecStart=/usr/local/bin/process-monitor --list
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## Quy Trình An Toàn

### Trước mọi thao tác nguy hiểm, PHẢI snapshot:
```bash
# Snapshot Test VM trước khi:
# - insmod module
# - make install (kernel)
# - update-grub
# - reboot với kernel mới

virsh snapshot-create-as TestVM "before-kernel-install-$(date +%Y%m%d-%H%M)"
```

### Nếu lỗi:
```bash
virsh snapshot-revert TestVM <snapshot-name>
```

---

## Checklist Demo Cuối Kỳ

- [ ] **Boot custom kernel**: `uname -r` hiển thị version tự build
- [ ] **Kernel module**: `lsmod | grep monitor` thấy module
- [ ] **ProcFS**: `cat /proc/process_monitor` hiển thị process list
- [ ] **User-space monitor**: Chương trình C đọc procfs và hiển thị
- [ ] **Socket server**: TCP multi-client chạy được, test bằng `nc` hoặc client
- [ ] **Scheduled backup**: Cron/systemd timer chạy tự động, có log
- [ ] **Minimal Ubuntu**: Boot thành công, service tự khởi động

---

## Stack Công Nghệ

| Layer | Công nghệ |
|---|---|
| Shell | Bash, cron, systemd timer |
| System C | POSIX API, epoll, mmap, inotify |
| Kernel | Linux Kernel Module, procfs, kbuild |
| VM | QEMU/KVM, virt-manager, libvirt |
| Build | debootstrap, make menuconfig, grub |

---

## Các Lệnh Hay Dùng

```bash
# Kiểm tra KVM
kvm-ok
egrep -c '(vmx|svm)' /proc/cpuinfo

# Quản lý VM
virt-manager
virsh list --all
virsh start DevVM
virsh snapshot-list TestVM

# Trong VM — kiểm tra module
lsmod
dmesg | tail -30
cat /proc/modules

# Trong VM — kiểm tra kernel
uname -r
uname -a
ls /boot/

# Debug build kernel
make -j$(nproc) 2>&1 | grep -E "error:|warning:"
```

---

## Ghi Chú Cho Agent

1. **Không bao giờ chạy `insmod`, `make install`, `update-grub` trên host** — chỉ trong VM
2. Khi viết kernel module, luôn include `MODULE_LICENSE("GPL")`
3. Mọi chương trình C cần compile sạch với `-Wall -Wextra`
4. Shell scripts cần `set -euo pipefail` và xử lý lỗi rõ ràng
5. Trước khi reboot Test VM, luôn tạo snapshot
6. `debootstrap` và kernel build chạy trong Dev VM, không phải host
7. Khi build kernel, dùng `make -j$(nproc)` để tận dụng CPU
8. Log mọi thao tác quan trọng vào `docs/progress.md`