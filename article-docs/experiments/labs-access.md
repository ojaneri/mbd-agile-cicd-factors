# Labs and hardware for this paper — access, where secrets live, lessons learned

Compiled 2026-11-11 from the author's earlier articles on janeri2 (read-only copy of their notes in
`docs/labs-from-server/`, source paths in [[experiments/labs-access]] §Sources) and from the author's
inventory spreadsheet (`Inventario Equipamentos EE.xlsx`, Downloads). **No secret is written here.**

## Where the secrets live (this PC, WSL Ubuntu, user root)
| Secret | Location | Copied from | Mode |
|---|---|---|---|
| FIT IoT-LAB CLI login | `~/.iotlabrc` | janeri2 `/root/.iotlabrc` | 600 |
| FIT IoT-LAB SSH key (frontends) | `~/.ssh/iotlab_ed25519` (+ `.pub`) | janeri2 `/root/.ssh/` | 600 |
| Shepherd Nova client login | `~/.config/shepherd/client.yaml` | janeri2 `/root/.config/shepherd/` | 600 |
Copied 2026-11-11 by scp over SSH (janeri2, port 2222); temporary copies deleted. Logins: IoT-LAB user
`janeri`; Shepherd account under the author's UTFPR address.

## Tools installed here
- IoT-LAB CLI: `/opt/iotlab-venv` (iotlabcli 3.3.2 + iotlabsshcli). **Verified 2026-11-11:** authenticated
  status query returned 10 alive `nrf52840dk` and 10 alive `st-iotnode` at Saclay.
- QEMU 10.2.1 (`mps2-an386`, Cortex-M4): development only, never a result (no real timing).
- Shepherd client: not installed here (lives in janeri2 `/opt/shepherd-venv`). Not needed for PIL.

## Targets for the PIL stage (decision d-0008, proposed)
1. **Primary: NUCLEO-L476RG (STM32L476RG, Cortex-M4F)**, owned by the author, on this PC.
   ST-LINK V2-1 virtual COM (was **COM3, 38400 baud**), mass-storage drive `NOD_L476RG` (was F:);
   flash by copying the `.bin`. Tooling from the earlier run: `C:\Users\osvaldo\Teste Claude\nucleo-l476rg\`
   (`capture.py COM3 … --flash F:`). **Not connected on 2026-11-11** (no COM3, no drive): needs a data
   USB cable (a charge-only cable gives Windows error 43).
2. **Replication: FIT IoT-LAB st-iotnode (STM32L475VG, same STM32L4 family)**. In the XAI-SDV work the
   same binary at 16 MHz gave cycle counts equal to the NUCLEO-L476RG's within a few cycles: a second
   physical board for free.
3. Not used: Shepherd Nova (energy, not needed), nRF52840 (different flash wait states), QEMU (dev only).

## Lessons learned that apply here (from the earlier articles)
- **IoT-LAB: submit the `.elf`, never `.hex`** (two `.hex` deployments failed, exp 450898/450899).
- **IoT-LAB serial: one TCP connection per node.** A leftover `nc` refuses later ones ("Connection
  refused"). Before retrying: `ssh -i ~/.ssh/iotlab_ed25519 janeri@saclay.iot-lab.info 'ps -u janeri -o pid,etime,cmd'`, kill stale `nc`.
- IoT-LAB console can truncate or merge lines: end every record with a checksum or length and drop
  incomplete lines. First connection right after `Running` may be refused while flashing: retry ~3 min.
- IoT-LAB etiquette: never hold all nodes of a site > 3 h on weekdays 9–19 h. Acknowledge "FIT IoT-LAB".
- MCU timing is deterministic (CV < 0.1 % in the XAI-SDV runs) — few repetitions suffice for cycles;
  runner noise matters only on the host stages.
- DWT cycle counter wraps (67 s at 64 MHz; 268 s at 16 MHz): accumulate wraps in software in long loops.
- STM32L4 at 16 MHz HSI runs with 0 flash wait states; that configuration is known-good and comparable
  across L475/L476.
- Earlier NUCLEO firmware was built on janeri2 with the pqm4/libopencm3 HAL; here we use a minimal
  register-level startup instead (no HAL dependency).

## Security note for the author (from the earlier notes, not verified here)
The XAI-SDV notes say the AWS notes directory under `admin.janeri.com.br/artigo/xai/docs/` is
web-served ("pending author action", 2026-09-25). If it still holds credentials, it may be public.

## Sources
Copied read-only from janeri2 `/var/lib/article-docs/tenants/u1/`:
- `ieee-its-xai-sdv-explainable-ai-for-safety-secur/article-docs/experiments/{labs-and-equipment,lab-candidates,mcu-cost}.md` and lab skills from its `skills.jsonl`
- `sae-brasil-kernel-seguro-e-tee-em-sdv/article-docs/experiments/pqc-benchmark-labs.md`, `experimentos/e3-pqc-mcu/README.md`
- `smartrtos-a-dual-plane-predictive-rtos-architect/article-docs/experiments/e-0001-measurement-protocol.md`
- `tinyml-based-cyberattack-detection-using-power-c/article-docs/experiments/e-000{1,2,3}-*.md`

## Decisions
- **[#d-0008]** date: 2026-11-11 · status: superseded · author: osvaldo · superseded_by: practice (boards used: FIT IoT-LAB st-iotnode and nRF52840; NUCLEO never used)
 · promoted_by: osvaldo on 2026-11-15
  **PIL target: NUCLEO-L476RG (local) as primary, FIT IoT-LAB st-iotnode as replication; QEMU for development only.**
  Why: local board has no queue, same Cortex-M4F as automotive S32K14x-class MCUs (to verify), and a
  second STM32L4 board in a public testbed lets a reviewer reproduce cycles. Rejected QEMU as a result
  source (no timing model). Cost: PIL needs the board plugged in; queue time on IoT-LAB must be reported
  apart from execution time.

## Todos
- **[#t-0038]** status: done · author: osvaldo — Closed 2026-11-15 as superseded: the NUCLEO board was not used; runs used FIT IoT-LAB boards. Original: Plug the NUCLEO-L476RG with a data cable; confirm COM port and drive letter.
- **[#t-0039]** status: done · author: osvaldo — Closed 2026-11-15: S32K is not mentioned in the paper. Original: Verify against NXP's datasheet that S32K14x uses a Cortex-M4F before writing it in the paper.
- **[#t-0040]** status: done · author: osvaldo — Done 2026-11-14: folder removed from the repository at the owner's request (history not rewritten). Original: Decide whether `docs/labs-from-server/` (contains login names and an e-mail) stays out of any anonymised artifact.
  Checked 2026-11-14: the folder is in the public `main` (since commit 40a4064, 2026-11-10). It holds the
  first author's UTFPR student e-mail (Shepherd account, 2 files), the IoT-LAB login and frontend hosts, the
  name (not the content) of the IoT-LAB SSH key file, and paths on the first author's server. No password,
  token or private key. None of it is needed by this paper. Proposed: remove the folder from `main` in the
  next commit (history keeps it unless rewritten, which needs the owner's explicit yes).
