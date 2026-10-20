from . import moc, ntpc
# 新增資料來源：在 adapters/ 新增模組（含 NAME、LABEL、fetch(today)->list[dict]），再加進這個清單
ADAPTERS = [moc, ntpc]
