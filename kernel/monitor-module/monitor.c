/*
 * Process Monitor Kernel Module
 * Exposes process information via /proc/process_monitor
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <linux/sched.h>
#include <linux/sched/signal.h>
#include <linux/mm.h>
#include <linux/version.h>

#define PROC_NAME "process_monitor"

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Student");
MODULE_DESCRIPTION("Process Monitor - Lists running processes with memory info");
MODULE_VERSION("1.0");

/*
 * seq_file show function - called for each read of /proc/process_monitor
 */
static int process_monitor_show(struct seq_file *m, void *v)
{
    struct task_struct *task;
    unsigned long vmrss;

    seq_printf(m, "%-8s %-20s %12s\n", "PID", "NAME", "VMRSS(kB)");
    seq_printf(m, "%-8s %-20s %12s\n", "---", "----", "---------");

    rcu_read_lock();
    for_each_process(task) {
        /* Get RSS (Resident Set Size) in kilobytes */
        vmrss = 0;
        if (task->mm) {
            vmrss = get_mm_rss(task->mm) << (PAGE_SHIFT - 10);
        }

        seq_printf(m, "%-8d %-20s %12lu\n",
                   task->pid,
                   task->comm,
                   vmrss);
    }
    rcu_read_unlock();

    return 0;
}

/*
 * seq_file open function
 */
static int process_monitor_open(struct inode *inode, struct file *file)
{
    return single_open(file, process_monitor_show, NULL);
}

/*
 * File operations structure for /proc entry
 */
#if LINUX_VERSION_CODE >= KERNEL_VERSION(5,6,0)
static const struct proc_ops process_monitor_fops = {
    .proc_open = process_monitor_open,
    .proc_read = seq_read,
    .proc_lseek = seq_lseek,
    .proc_release = single_release,
};
#else
static const struct file_operations process_monitor_fops = {
    .owner = THIS_MODULE,
    .open = process_monitor_open,
    .read = seq_read,
    .llseek = seq_lseek,
    .release = single_release,
};
#endif

/*
 * Module initialization
 */
static int __init process_monitor_init(void)
{
    struct proc_dir_entry *entry;

    entry = proc_create(PROC_NAME, 0444, NULL, &process_monitor_fops);
    if (!entry) {
        pr_err("process_monitor: Failed to create /proc/%s\n", PROC_NAME);
        return -ENOMEM;
    }

    pr_info("process_monitor: Module loaded, /proc/%s created\n", PROC_NAME);
    return 0;
}

/*
 * Module cleanup
 */
static void __exit process_monitor_exit(void)
{
    remove_proc_entry(PROC_NAME, NULL);
    pr_info("process_monitor: Module unloaded, /proc/%s removed\n", PROC_NAME);
}

module_init(process_monitor_init);
module_exit(process_monitor_exit);
