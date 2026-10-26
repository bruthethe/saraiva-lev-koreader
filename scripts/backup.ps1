# READ-ONLY backup of the device partitions (nanda..nandf) with md5 verification.
# nandg (books) is not copied. Keep the backup OUT of cloud-synced folders: nande holds the
# device identity (serial, MAC) and the user partition can hold Wi-Fi passwords / DRM data.
# Usage: .\scripts\backup.ps1 -Destination D:\lev-backup      (needs adb in PATH, ~1.1 GB free)
param([Parameter(Mandatory)][string]$Destination)
New-Item -ItemType Directory -Force $Destination | Out-Null
foreach ($p in 'nanda','nandb','nandc','nandd','nande','nandf') {
    adb pull /dev/$p "$Destination\$p.img" | Out-Null
    $local  = (Get-FileHash "$Destination\$p.img" -Algorithm MD5).Hash.ToLower()
    $device = (adb shell "md5sum /dev/$p").Trim().Split(' ')[0]
    '{0}: {1}' -f $p, $(if ($local -eq $device) { 'OK' } else { "MISMATCH ($local vs $device)" })
}
