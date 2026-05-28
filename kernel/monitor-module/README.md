# Process Monitor Kernel Module

## Mô Tả

Module kernel Linux theo dõi các process đang chạy và expose thông tin qua `/proc/process_monitor`.

## Thông Tin Hiển Thị

- **PID**: Process ID
- **NAME**: Tên process (comm)
- **VMRSS(kB)**: Resident Set Size (bộ nhớ vật lý đang dùng) tính bằng kilobytes

## Build Module

```bash
cd kernel/monitor-module
make
```

Output sẽ tạo file `monitor.ko`.

## Load Module (trong VM)

**⚠️ QUAN TRỌNG: Snapshot VM trước khi load module!**

```bash
# Load module
sudo insmod monitor.ko

# Kiểm tra module đã load
lsmod | grep monitor

# Xem kernel log
dmesg | tail -20
```

## Sử Dụng

Đọc thông tin process:

```bash
cat /proc/process_monitor
```

Output mẫu:
```
PID      NAME                 VMRSS(kB)
---      ----                 ---------
1        systemd                   4096
2        kthreadd                     0
123      bash                      2048
456      sshd                      3072
...
```

## Unload Module

```bash
# Remove module
sudo rmmod monitor

# Kiểm tra đã remove
lsmod | grep monitor

# Xem kernel log
dmesg | tail -10
```

## Cấu Trúc Code

- **process_monitor_show()**: Hàm chính duyệt qua tất cả process và ghi vào seq_file
- **for_each_process()**: Macro kernel duyệt task_struct list
- **get_mm_rss()**: Lấy RSS từ mm_struct
- **proc_create()**: Tạo entry trong /proc filesystem
- **seq_file API**: Interface chuẩn để xuất dữ liệu lớn qua procfs

## Tương Thích Kernel

Module hỗ trợ cả kernel cũ và mới:
- Kernel >= 5.6: dùng `proc_ops`
- Kernel < 5.6: dùng `file_operations`

## Makefile Targets

| Target | Mô tả |
|--------|-------|
| `make` hoặc `make all` | Build module |
| `make clean` | Xóa file build |
| `make install` | Load module (cần sudo) |
| `make uninstall` | Unload module (cần sudo) |
| `make test` | Đọc /proc/process_monitor |

## Troubleshooting

### Module không load được
```bash
# Kiểm tra lỗi chi tiết
dmesg | tail -30

# Kiểm tra kernel headers đã cài
ls /lib/modules/$(uname -r)/build
```

### Không thấy /proc/process_monitor
```bash
# Kiểm tra module đã load
lsmod | grep monitor

# Kiểm tra procfs
ls -la /proc/ | grep process
```

### Kernel panic sau khi load
- Restore VM từ snapshot
- Kiểm tra lại code, đặc biệt phần truy cập task->mm
- Build lại với debug symbols: thêm `EXTRA_CFLAGS=-g` vào Makefile

## Lưu Ý An Toàn

1. **Luôn snapshot VM trước khi insmod**
2. **Không load trên host** - chỉ trong VM
3. **Test trên Test VM**, không phải Dev VM đang build
4. Nếu kernel panic, restore snapshot ngay
5. Kiểm tra `dmesg` sau mỗi lần load/unload

## Kiến Thức Liên Quan

- **RCU (Read-Copy-Update)**: Cơ chế đồng bộ kernel, dùng `rcu_read_lock()`
- **task_struct**: Cấu trúc dữ liệu mô tả process trong kernel
- **mm_struct**: Quản lý memory của process
- **seq_file**: API để xuất dữ liệu tuần tự qua procfs
- **procfs**: Pseudo-filesystem expose thông tin kernel
