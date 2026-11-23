"""独立于界面的 JSON 名单存储。"""

import hashlib
import json
import os
import re
import uuid
from pathlib import Path


def clean_students(names):
    """清理空值并按原顺序去重，避免同一联系人被重复发送。"""
    result = []
    seen = set()
    for name in names:
        name = name.strip()
        if len(name) == 1:
            name += "同学"
        if name and name not in seen:
            result.append(name)
            seen.add(name)
    return result


class RosterStore:
    def __init__(self, directory):
        self.directory = Path(directory)

    def make_roster(self, name, subject, students, source_file=""):
        source_file = os.path.abspath(source_file) if source_file else ""
        # 同一 Excel 的不同科目独立保存；同名但不同路径的文件互不覆盖。
        identity = f"{os.path.normcase(source_file) if source_file else name}\0{subject}"
        digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12]
        label = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", f"{name}-{subject}")
        return {
            "id": f"roster-{label[:60].strip(' .')}-{digest}",
            "name": name,
            "subject": subject,
            "source_file": source_file,
            "students": clean_students(students),
            "excluded_students": [],
        }

    def copy_roster(self, original, name, students):
        """另存为独立名单；保留来源与排除标记，不复用 Excel 导入身份。"""
        roster = self.make_roster(name, original.get("subject", ""), students)
        roster["id"] += f"-copy-{uuid.uuid4().hex[:12]}"
        roster["source_file"] = original.get("source_file", "")
        roster["excluded_students"] = list(original["excluded_students"])
        return roster

    @staticmethod
    def validate(data, roster_id):
        if not isinstance(data, dict) or data.get("version") != 1:
            raise ValueError("不支持的名单格式或版本")
        if not isinstance(data.get("name"), str) or not data["name"].strip():
            raise ValueError("名单名称不能为空")
        for field in ("subject", "source_file"):
            if not isinstance(data.get(field, ""), str):
                raise ValueError(f"{field} 必须是文本")
        for field in ("students", "excluded_students"):
            names = data.get(field, [])
            if not isinstance(names, list) or any(not isinstance(n, str) for n in names):
                raise ValueError(f"{field} 必须是姓名数组")
        result = dict(data, id=roster_id)
        result["students"] = clean_students(data.get("students", []))
        excluded = set(clean_students(data.get("excluded_students", [])))
        result["excluded_students"] = [n for n in result["students"] if n in excluded]
        return result

    def load_all(self):
        rosters, errors = {}, []
        if not self.directory.exists():
            return rosters, errors
        for path in sorted(self.directory.glob("*.json")):
            try:
                with path.open("r", encoding="utf-8-sig") as stream:
                    roster = self.validate(json.load(stream), path.stem)
                rosters[path.stem] = roster
            except (OSError, ValueError, TypeError) as exc:
                errors.append(f"{path.name}：{exc}")
        return rosters, errors

    def save(self, roster):
        roster_id = roster["id"]
        if not re.fullmatch(r"roster-[^<>:\"/\\|?*\x00-\x1f]+", roster_id) or roster_id.endswith((".", " ")):
            raise ValueError("无效的名单文件名")
        data = self.validate(dict(roster, version=1), roster_id)
        self.directory.mkdir(parents=True, exist_ok=True)
        target = self.directory / f"{roster_id}.json"
        temporary = target.with_suffix(".json.tmp")
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary, target)
        return data
