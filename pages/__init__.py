
from .power_off import PagePowerOff

power_off_page = PagePowerOff()

def get_pages(page_names):
    pages = []
    for name in page_names:
        if "battery" == name:
            from .battery import PageBattery
            pages.append(PageBattery())
        elif "disk" == name:
            from .disks import PageDisks
            pages.append(PageDisks())
        elif "input" == name:
            from .input import PageInput
            pages.append(PageInput())
        elif "ips" == name:
            from .ips import PageIPs
            pages.append(PageIPs())
        elif "mix" == name:
            from .mix import PageMix
            pages.append(PageMix())
        elif "rpi_power" == name:
            from .rpi_power import PageRPiPower
            pages.append(PageRPiPower())
        elif "performance" == name:
            from .performance import PagePerformance
            pages.append(PagePerformance())
        elif "orchestrator" == name:
            from .orchestrator import PageOrchestrator
            pages.append(PageOrchestrator())
        elif "docker_health" == name:
            from .docker_health import PageDockerHealth
            pages.append(PageDockerHealth())
        elif "network" == name:
            from .network_status import PageNetwork
            pages.append(PageNetwork())
        elif "backup" == name:
            from .backup_status import PageBackupStatus
            pages.append(PageBackupStatus())
        elif "nvme" == name:
            from .nvme_health import PageNVMeHealth
            pages.append(PageNVMeHealth())
        else:
            raise ValueError(f"Unknown page name: {name}")

    return pages
