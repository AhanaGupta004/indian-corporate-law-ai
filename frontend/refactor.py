import os
import re
import shutil
from pathlib import Path

SRC_DIR = Path(r"c:\Users\Panka\OneDrive\Desktop\legalbuddy\frontend\src")

# 1. Define file mappings (old relative to src -> new relative to src)
FILE_MAP = {
    # Core
    "App.jsx": "core/App.jsx",
    "components/Layout.jsx": "core/LayoutView.jsx",
    "components/Sidebar.jsx": "core/SidebarView.jsx",
    "components/Header.jsx": "core/TopBarView.jsx", # Assuming Header is Topbar or just map it
    "main.jsx": "main.jsx", # Remains

    # Auth
    "components/Login.jsx": "features/auth/views/LoginView.jsx",
    "store/authStore.js": "features/auth/models/authStore.js",

    # Documents
    "components/DocumentsView.jsx": "features/documents/views/DocumentsView.jsx",
    "components/DocumentFiles.jsx": "features/documents/views/DocumentFilesView.jsx",
    "components/FileViewer.jsx": "features/documents/views/FileViewerView.jsx",
    "components/PDFViewer.jsx": "features/documents/views/PDFViewerView.jsx",
    "components/UploadArea.jsx": "features/documents/views/UploadAreaView.jsx",
    "components/AnalysisResult.jsx": "features/documents/views/AnalysisResultView.jsx",
    "components/RecentFiles.jsx": "features/documents/views/RecentFilesView.jsx",
    "components/SampleDocuments.jsx": "features/documents/views/SampleDocumentsView.jsx",
    "store/fileStore.js": "features/documents/models/fileStore.js",
    "hooks/useFileUpload.js": "features/documents/intents/useFileUpload.js",
    "hooks/useDocumentFetch.js": "features/documents/intents/useDocumentFetch.js",
    "hooks/useAnalysisPolling.js": "features/documents/intents/useAnalysisPolling.js",

    # Support
    "components/SupportPage.jsx": "features/support/views/SupportView.jsx",

    # Dashboard
    "components/Dashboard.jsx": "features/dashboard/views/DashboardView.jsx",
    "hooks/useGreeting.js": "features/dashboard/intents/useGreeting.js",
    
    # Billing / Subscription
    "components/Subscription.jsx": "features/billing/views/SubscriptionView.jsx",
    "components/Usage.jsx": "features/billing/views/UsageView.jsx",
    "components/StripeCheckoutModal.jsx": "features/billing/views/StripeCheckoutModal.jsx",

    # Admin
    "components/AdminPanel.jsx": "features/admin/views/AdminPanelView.jsx",
    "components/admin/AdminOverview.jsx": "features/admin/views/AdminOverviewView.jsx",
    "components/admin/AdminAgents.jsx": "features/admin/views/AdminAgentsView.jsx",
    "components/admin/AdminTickets.jsx": "features/admin/views/AdminTicketsView.jsx",
    "components/admin/AdminAgentDetail.jsx": "features/admin/views/AdminAgentDetailView.jsx",
    "components/admin/AdminTicketDetail.jsx": "features/admin/views/AdminTicketDetailView.jsx",

    # Shared UI / Utils
    "components/Loader.jsx": "shared/ui/Loader.jsx",
    "components/HeroSection.jsx": "shared/ui/HeroSection.jsx",
    "components/TabSection.jsx": "shared/ui/TabSection.jsx",
    "components/shared/FeatureCard.jsx": "shared/ui/FeatureCard.jsx",
    "components/shared/ListSection.jsx": "shared/ui/ListSection.jsx",
    "components/shared/StatCard.jsx": "shared/ui/StatCard.jsx",
    "components/shared/TabButton.jsx": "shared/ui/TabButton.jsx",
    "components/shared/TextViewer.jsx": "shared/ui/TextViewer.jsx",
    "components/shared/index.jsx": "shared/ui/index.jsx",
    
    "store/uiStore.js": "shared/store/uiStore.js",
    "utils/api.js": "shared/utils/api.js",
    "utils/storage.js": "shared/utils/storage.js",
    "utils/sampleDocuments.js": "shared/utils/sampleDocuments.js",
    
    # Empty index files for hooks
    "hooks/index.js": "shared/utils/index.js",
}

def resolve_path(current_file_dir, import_path):
    # Returns path relative to src/
    if not import_path.startswith("."):
        return import_path
    
    # Handle extension omission
    # Just normalize path assuming it exists
    base = current_file_dir / import_path
    return os.path.normpath(base).replace("\\", "/")

def get_rel_path(from_file, to_file):
    from_dir = Path(from_file).parent
    to_p = Path(to_file)
    try:
        rel = os.path.relpath(to_p, from_dir)
        rel = rel.replace("\\", "/")
        if not rel.startswith("."):
            rel = "./" + rel
        
        # Remove .jsx or .js extension for imports
        if rel.endswith(".jsx"):
            rel = rel[:-4]
        elif rel.endswith(".js"):
            rel = rel[:-3]
        return rel
    except Exception:
        return to_file

# Create mapping dictionary without extensions for matching
# map: src_relative_without_ext -> new_src_relative_without_ext
extless_map = {}
for old, new in FILE_MAP.items():
    old_extless = re.sub(r'\.jsx?$', '', old)
    extless_map[old_extless] = new

# 2. Build directories & Move files
for old_rel, new_rel in FILE_MAP.items():
    old_path = SRC_DIR / old_rel
    new_path = SRC_DIR / new_rel
    if old_path.exists() and old_path != new_path:
        new_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old_path), str(new_path))
        print(f"Moved {old_rel} -> {new_rel}")

# 3. Rewrite imports
# Import regex: import ... from '...' or import '...'
import_pattern = re.compile(r"(from\s+['\"]|import\s+['\"])([^'\"]+)(['\"])")

def update_imports(file_path, new_rel_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return
        
    def replace_match(match):
        prefix = match.group(1)
        imp_path = match.group(2)
        suffix = match.group(3)
        
        if not imp_path.startswith("."):
            return match.group(0) # Not a local import
            
        # Old absolute (relative to src)
        old_abs_dir = Path(new_rel_path).parent # Because file is already moved, wait, no. The imports in the file were written relative to OLD path.
        # Wait, if we moved the file, the text inside still assumes OLD location.
        # So we resolve using OLD location!
        
        # Find old path of THIS file
        old_this = next((k for k, v in FILE_MAP.items() if v == new_rel_path), new_rel_path)
        old_this_dir = Path(old_this).parent
        
        # Resolve target's old path
        target_old_abs = resolve_path(old_this_dir, imp_path)
        
        # Map target's old path to new path
        target_new = extless_map.get(target_old_abs, target_old_abs)
        
        # If target didn't move (not in map), it might be an asset like '../assets/logo.svg'
        if target_new == target_old_abs:
            # Just calculate relative from new_rel_path to target_old_abs
            target_new_full = target_old_abs
        else:
            target_new_full = target_new
            
        # Calculate new relative path
        new_imp = get_rel_path(new_rel_path, target_new_full)
        return prefix + new_imp + suffix

    new_content = import_pattern.sub(replace_match, content)
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated imports in {new_rel_path}")

# Run on all files
for root, dirs, files in os.walk(SRC_DIR):
    for f in files:
        if f.endswith('.js') or f.endswith('.jsx'):
            full_path = Path(root) / f
            rel_path = full_path.relative_to(SRC_DIR).as_posix()
            update_imports(full_path, rel_path)

# Cleanup empty dirs
def remove_empty_dirs(path):
    for root, dirs, files in os.walk(path, topdown=False):
        for name in dirs:
            try:
                os.rmdir(os.path.join(root, name))
            except OSError:
                pass

remove_empty_dirs(SRC_DIR)
print("Done!")
