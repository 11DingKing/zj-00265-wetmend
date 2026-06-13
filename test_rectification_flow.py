import urllib.request
import urllib.error
import json
import sys

BASE = "http://127.0.0.1:8001"


def get(path):
    req = urllib.request.Request(BASE + path)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def post(path, data):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {e.read().decode()}")
        raise


def put(path, data):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=body, headers={"Content-Type": "application/json"}, method="PUT")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main():
    print("=== 1. 根接口 ===")
    print(json.dumps(get("/"), ensure_ascii=False, indent=2))

    print("\n=== 2. 查看项目3(甘南玛曲)当前状态 ===")
    p = get("/projects/3")
    print(f"  项目名: {p['name']}, 状态: {p['status']}, 目标植被覆盖度: {p['target_vegetation_coverage']}")

    print("\n=== 3. 项目3验收预览(第一轮，目标90%但监测最高82.5%，应该未达标) ===")
    prev = get("/acceptances/preview/3")
    print(f"  overall_reached={prev['overall_reached']}, can_accept={prev['can_accept']}, reason={prev['reason']}")
    for c in prev["comparisons"]:
        print(f"    {c['indicator_name']}: 目标 {c['target_value']}, 实际 {c['actual_value']}, 达标={c['reached']}")

    print("\n=== 4. 创建第一轮验收(应该被判为需延期整改，状态自动进入整改期) ===")
    acc1 = post("/acceptances/", {"project_id": 3, "acceptance_date": "2025-08-01", "extension_days": 60, "remarks": "植被覆盖度未达标，需整改补种"})
    print(f"  验收轮次: {acc1['round']}, 结果: {acc1['result']}, 状态流转后项目状态待查询")
    p = get("/projects/3")
    print(f"  项目当前状态: {p['status']}")

    print("\n=== 5. 登记整改方案 ===")
    plan = post("/rectification-plans/", {
        "project_id": 3,
        "acceptance_id": acc1["id"],
        "plan_content": "1) 对退化严重地块进行乡土草本补播；2) 加强生态补水；3) 围栏封育禁止放牧；4) 每两月跟踪监测一次",
        "rectification_deadline": "2025-10-01",
        "responsible_person": "扎西主任",
        "notes": "优先落实引水沟渠和补播工作"
    })
    print(f"  整改方案ID: {plan['id']}, 状态: {plan['status']}, 截止: {plan['rectification_deadline']}")

    print("\n=== 6. 整改期内补充录入监测数据(目标是让植被覆盖度超过90%) ===")
    # 项目3有两个地块 id=5,6
    mr1 = post("/monitoring-records/", {
        "plot_id": 5, "record_date": "2025-09-15",
        "vegetation_coverage": 91.5, "carbon_sequestration": 52.0, "water_conservation": 310.0,
        "notes": "整改后复查，植被显著恢复"
    })
    mr2 = post("/monitoring-records/", {
        "plot_id": 6, "record_date": "2025-09-15",
        "vegetation_coverage": 90.8, "carbon_sequestration": 50.5, "water_conservation": 305.0,
        "notes": "整改后复查"
    })
    print(f"  新增监测记录ID: {mr1['id']}, {mr2['id']}")

    print("\n=== 7. 完成整改，项目从整改期回到监测期 ===")
    p = post(f"/rectification-plans/{plan['id']}/complete", None)
    print(f"  整改完成后项目状态: {p['status']}")
    plan_check = get(f"/rectification-plans/{plan['id']}")
    print(f"  整改方案状态: {plan_check['status']}, 完成日期: {plan_check['completion_date']}")

    print("\n=== 8. 第二轮验收预览(整改后应该达标) ===")
    prev2 = get("/acceptances/preview/3")
    print(f"  overall_reached={prev2['overall_reached']}, can_accept={prev2['can_accept']}, reason={prev2['reason']}")
    for c in prev2["comparisons"]:
        print(f"    {c['indicator_name']}: 目标 {c['target_value']}, 实际 {c['actual_value']}, 达标={c['reached']}")

    print("\n=== 9. 发起第二轮验收(应判为达标，状态进入验收) ===")
    acc2 = post("/acceptances/", {"project_id": 3, "acceptance_date": "2025-10-05", "remarks": "整改后指标全面达标"})
    print(f"  验收轮次: {acc2['round']}, 结果: {acc2['result']}")
    p = get("/projects/3")
    print(f"  项目最终状态: {p['status']}")
    print(f"  项目所有验收记录轮次: {[(a['round'], a['result']) for a in p['acceptances']]}")

    print("\n=== 10. 验证达标统计：整改后才达标的项目应被计入 passed_projects ===")
    stats_region = get("/statistics/by-region")
    for s in stats_region:
        if s["region"] == "甘肃省甘南藏族自治州":
            print(f"  甘南州: 总项目 {s['total_projects']}, 达标 {s['passed_projects']}")
            assert s["passed_projects"] >= 1, "整改后达标项目未被统计！"

    stats_type = get("/statistics/by-degradation-type")
    for s in stats_type:
        print(f"  {s['degradation_type']}: 总项目 {s['total_projects']}, 达标 {s['passed_projects']}")

    print("\n=== 11. 验证：已达标项目不能再重复发起验收 ===")
    try:
        post("/acceptances/", {"project_id": 3, "acceptance_date": "2025-10-06"})
        print("  错误：已达标项目不应允许再次验收！")
        sys.exit(1)
    except urllib.error.HTTPError as e:
        print(f"  正确拦截，HTTP {e.code}")

    print("\n=== 12. 验证措施成效统计也能正确统计整改后达标项目 ===")
    eff = get("/statistics/by-measure-effectiveness")
    print(f"  摘要: {eff['summary']}")
    for item in eff["data"]:
        print(f"  {item['measure_type']}: 项目数 {item['total_projects']}, 达标数 {item['total_passed_projects']}, 通过率 {item['pass_rate']}%")

    print("\n✅ 整改支线全流程验证通过！")


if __name__ == "__main__":
    main()
