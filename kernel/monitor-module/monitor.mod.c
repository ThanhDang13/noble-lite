#include <linux/module.h>
#include <linux/export-internal.h>
#include <linux/compiler.h>

MODULE_INFO(name, KBUILD_MODNAME);

__visible struct module __this_module
__section(".gnu.linkonce.this_module") = {
	.name = KBUILD_MODNAME,
	.init = init_module,
#ifdef CONFIG_MODULE_UNLOAD
	.exit = cleanup_module,
#endif
	.arch = MODULE_ARCH_INIT,
};



static const struct modversion_info ____versions[]
__used __section("__versions") = {
	{ 0xce105414, "single_open" },
	{ 0x0d8b6c91, "seq_printf" },
	{ 0xd272d446, "__rcu_read_lock" },
	{ 0x5f41ea90, "init_task" },
	{ 0xd272d446, "__rcu_read_unlock" },
	{ 0xcdeafffc, "remove_proc_entry" },
	{ 0x11bacf83, "seq_read" },
	{ 0xd5bc7086, "seq_lseek" },
	{ 0x024d45a2, "single_release" },
	{ 0xd272d446, "__fentry__" },
	{ 0x92878b20, "proc_create" },
	{ 0xe8213e80, "_printk" },
	{ 0xd272d446, "__x86_return_thunk" },
	{ 0x814e12e5, "module_layout" },
};

static const u32 ____version_ext_crcs[]
__used __section("__version_ext_crcs") = {
	0xce105414,
	0x0d8b6c91,
	0xd272d446,
	0x5f41ea90,
	0xd272d446,
	0xcdeafffc,
	0x11bacf83,
	0xd5bc7086,
	0x024d45a2,
	0xd272d446,
	0x92878b20,
	0xe8213e80,
	0xd272d446,
	0x814e12e5,
};
static const char ____version_ext_names[]
__used __section("__version_ext_names") =
	"single_open\0"
	"seq_printf\0"
	"__rcu_read_lock\0"
	"init_task\0"
	"__rcu_read_unlock\0"
	"remove_proc_entry\0"
	"seq_read\0"
	"seq_lseek\0"
	"single_release\0"
	"__fentry__\0"
	"proc_create\0"
	"_printk\0"
	"__x86_return_thunk\0"
	"module_layout\0"
;

MODULE_INFO(depends, "");


MODULE_INFO(srcversion, "21C3FCA609BBA38BA4D9FFA");
