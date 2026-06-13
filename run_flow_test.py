import sys
sys.path.insert(0, "/Users/ding/Documents/SOLOCODE 3/0612/macmini/zj-00265-wetmend-4")

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_rectification_flow():
    print("=== 1. 根接口 ===")
    r = client.get("/")
    print(r.json())

    print("\n=== 2. 查看项目3(甘南玛曲)当前状态 ===")
    r = client.get("/projects/3")
    p = r.json()
    print(f"  项目名: {p['name']}, 状态: {p['status']}, 目标植被覆盖度: {p['target_vegetation_coverage']}")

    print("\n=== 3. 项目3验收预览 ===")
    r = client.get("/acceptances/preview/3")
    if r.status_code != 200:
        print(f"  ERROR {r.status_code}: {r.text}")
        return
    prev = r.json()
    print(f"  overall_reached={prev['overall_reached']}, can_accept={prev['can_accept']}, reason={prev['reason']}")
    for c in prev["comparisons"]:
        print(f"    {c['indicator_name']}: 目标 {c['target_value']}, 实际 {c['actual_value']}, 达标={c['reached']}")

    print("\n=== 4. 创建第一轮验收(应被判为需延期整改，状态自动进入整改期) ===")
    r = client.post("/acceptances/", json={"project_id": 3, "acceptance_date": "2025-08-01", "extension_days": 60, "remarks": "植被覆盖度未达标"})
    if r.status_code != 200:
        print(f"  ERROR {r.status_code}: {r.text}")
        return
    acc1 = r.json()
    print(f"  验收ID: {acc1['id']}, 轮次: {acc1['round']}, 结果: {acc1['result']}")
    p = client.get("/projects/3").json()
    print(f"  项目当前状态: {p['status']}")

    print("\n=== 5. 登记整改方案 ===")
    r = client.post("/rectification-plans/", json={
        "project_id": 3,
        "acceptance_id": acc1["id"],
        "plan_content": "补播+生态补水+围栏封育",
        "rectification_deadline": "2025-10-01",
        "responsible_person": "扎西主任"
    })
    if r.status_code != 200:
        print(f"  ERROR {r.status_code}: {r.text}")
        return
    plan = r.json()
    print(f"  整改方案ID: {plan['id']}, 状态: {plan['status']}, 截止: {plan['rectification_deadline']}")

    print("\n=== 6. 整改期内录入监测数据 ===")
    r1 = client.post("/monitoring-records/", json={
        "plot_id": 5, "record_date": "2025-09-15",
        "vegetation_coverage": 91.5, "carbon_sequestration": 52.0, "water_conservation": 310.0
    })
    r2 = client.post("/monitoring-records/", json={
        "plot_id": 6, "record_date": "2025-09-15",
        "vegetation_coverage": 90.8, "carbon_sequestration": 50.5, "water_conservation": 305.0
    })
    assert r1.status_code == 200 and r2.status_code == 200, f"监测录入失败: {r1.status_code} {r1.text} / {r2.status_code} {r2.text}"
    print(f"  监测记录ID: {r1.json()['id']}, {r2.json()['id']}")

    print("\n=== 7. 完成整改 → 回到监测期 ===")
    r = client.post(f"/rectification-plans/{plan['id']}/complete")
    if r.status_code != 200:
        print(f"  ERROR {r.status_code}: {r.text}")
        return
    p = r.json()
    print(f"  整改后项目状态: {p['status']}")

    print("\n=== 8. 第二轮验收预览 ===")
    prev2 = client.get("/acceptances/preview/3").json()
    print(f"  overall_reached={prev2['overall_reached']}, can_accept={prev2['can_accept']}")

    print("\n=== 9. 第二轮验收(应达标) ===")
    r = client.post("/acceptances/", json={"project_id": 3, "acceptance_date": "2025-10-05"})
    if r.status_code != 200:
        print(f"  ERROR {r.status_code}: {r.text}")
        return
    acc2 = r.json()
    print(f"  轮次: {acc2['round']}, 结果: {acc2['result']}")
    p = client.get("/projects/3").json()
    print(f"  项目最终状态: {p['status']}")
    print(f"  验收记录: {[(a['round'], a['result']) for a in p['acceptances']]}")

    print("\n=== 10. 统计中正确计入整改后达标项目 ===")
    region = client.get("/statistics/by-region").json()
    for s in region:
        if s["region"] == "甘肃省甘南藏族自治州":
            print(f"  甘南州: 总项目 {s['total_projects']}, 达标 {s['passed_projects']}")
            assert s["passed_projects"] >= 1

    stats_type = client.get("/statistics/by-degradation-type").json()
    for s in stats_type:
        print(f"  {s['degradation_type']}: 总项目 {s['total_projects']}, 达标 {s['passed_projects']}")

    print("\n=== 11. 已达标项目不能再次验收 ===")
    r = client.post("/acceptances/", json={"project_id": 3, "acceptance_date": "2025-10-06"})
    assert r.status_code == 400, f"应拦截重复达标验收, 实际 {r.status_code}"
    print(f"  正确拦截 HTTP {r.status_code}")

    print("\n=== 12. 措施成效统计联动 ===")
    eff = client.get("/statistics/by-measure-effectiveness").json()
    print(f"  摘要: {eff['summary']}")
    for item in eff["data"]:
        print(f"  {item['measure_type']}: 项目 {item['total_projects']}, 达标 {item['total_passed_projects']}, 通过率 {item['pass_rate']}%")

    print("\n✅ 整改支线全流程验证通过！")


if __name__ == "__main__":
    test_rectification_flow()
