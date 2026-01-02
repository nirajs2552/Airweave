import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Loader2, Folder, File, Upload, RefreshCw, ChevronRight, ChevronLeft, Send } from 'lucide-react';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api';
import { cn } from '@/lib/utils';

interface FileItem {
  id: string;
  name: string;
  path: string;
  size?: number;
  modified_at?: string;
  type: string;
  mime_type?: string;
}

interface FolderItem {
  id: string;
  name: string;
  path: string;
  type: string;
}

interface BrowseResponse {
  files: FileItem[];
  folders: FolderItem[];
  current_path?: string;
  parent_path?: string;
}

// Supported document file types
const DOCUMENT_FILE_EXTENSIONS = [
  '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
  '.txt', '.csv', '.rtf', '.odt', '.ods', '.odp',
  '.html', '.htm', '.xml', '.json', '.md'
];

const isDocumentFile = (fileName: string, mimeType?: string): boolean => {
  const ext = fileName.toLowerCase().substring(fileName.lastIndexOf('.'));
  if (DOCUMENT_FILE_EXTENSIONS.includes(ext)) {
    return true;
  }
  // Also check MIME type for document files
  if (mimeType) {
    const docMimeTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-powerpoint',
      'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      'text/plain',
      'text/csv',
      'text/html',
      'application/xml',
      'application/json',
      'text/markdown',
    ];
    return docMimeTypes.some(mt => mimeType.toLowerCase().includes(mt.toLowerCase()));
  }
  return false;
};

interface FileBrowserProps {
  sourceConnectionId: string;
  collectionId: string; // Can be readable_id or UUID
  onFilesSelected?: (fileIds: string[]) => void;
  isDark?: boolean;
}

export function FileBrowser({
  sourceConnectionId,
  collectionId,
  onFilesSelected,
  isDark = false,
}: FileBrowserProps) {
  const [browseData, setBrowseData] = useState<BrowseResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [currentFolderId, setCurrentFolderId] = useState<string | null>(null);
  const [driveId, setDriveId] = useState<string | null>(null);
  const [siteId, setSiteId] = useState<string | null>(null);
  const [browseLevel, setBrowseLevel] = useState<'sites' | 'drives' | 'files'>('sites');
  const [isUploading, setIsUploading] = useState(false);
  const [collectionUuid, setCollectionUuid] = useState<string | null>(null);

  // Fetch collection UUID from readable_id if needed
  useEffect(() => {
    const fetchCollectionUuid = async () => {
      // Check if collectionId is already a UUID (format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
      const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
      if (uuidRegex.test(collectionId)) {
        setCollectionUuid(collectionId);
        return;
      }

      // Otherwise, it's a readable_id, fetch the collection to get UUID
      try {
        const response = await apiClient.get(`/collections/${collectionId}`);
        if (response.ok) {
          const collection = await response.json();
          setCollectionUuid(collection.id);
        } else {
          console.error('Failed to fetch collection:', await response.text());
        }
      } catch (error) {
        console.error('Error fetching collection UUID:', error);
      }
    };

    if (collectionId) {
      fetchCollectionUuid();
    }
  }, [collectionId]);

  const fetchFiles = async (folderId?: string | null, driveIdParam?: string | null, siteIdParam?: string | null) => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      if (siteIdParam) params.append('site_id', siteIdParam);
      if (driveIdParam) params.append('drive_id', driveIdParam);
      if (folderId) params.append('folder_id', folderId);

      const response = await apiClient.get(
        `/file-browser/${sourceConnectionId}/browse?${params.toString()}`
      );

      if (!response.ok) {
        throw new Error('Failed to browse files');
      }

      const data: BrowseResponse = await response.json();
      
      // Determine browse level from current_path
      if (data.current_path === '/sites' || (!data.current_path && !siteIdParam && !driveIdParam)) {
        setBrowseLevel('sites');
      } else if (data.current_path?.includes('/drives') && !folderId && data.files.length === 0 && data.folders.length > 0) {
        setBrowseLevel('drives');
      } else {
        setBrowseLevel('files');
      }
      
      // Filter to show only document files (only when browsing files, not sites/drives)
      const documentFiles = browseLevel === 'files' 
        ? data.files.filter(file => isDocumentFile(file.name, file.mime_type))
        : data.files;
      
      setBrowseData({
        ...data,
        files: documentFiles,
      });

      // Extract IDs from current_path
      if (data.current_path) {
        const siteMatch = data.current_path.match(/\/sites\/([^\/]+)/);
        if (siteMatch) {
          setSiteId(siteMatch[1]);
        }
        
        const driveMatch = data.current_path.match(/\/drives\/([^\/]+)/);
        if (driveMatch) {
          setDriveId(driveMatch[1]);
        }
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to browse files');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, [sourceConnectionId]);

  const handleFolderClick = (folderId: string, folderPath?: string) => {
    // Determine what level we're navigating to based on the path
    if (folderPath?.startsWith('/sites/') && !folderPath.includes('/drives/')) {
      // Clicking on a site - show its drives
      setSiteId(folderId);
      setDriveId(null);
      setCurrentFolderId(null);
      fetchFiles(null, null, folderId);
    } else if (folderPath?.includes('/drives/') && !folderPath.includes('/items/')) {
      // Clicking on a drive - show its files/folders (root level)
      // Extract drive_id from path like /sites/{site_id}/drives/{drive_id}
      const driveMatch = folderPath.match(/\/drives\/([^\/]+)/);
      if (driveMatch) {
        setDriveId(driveMatch[1]);
        setCurrentFolderId(null);
        fetchFiles(null, driveMatch[1], siteId);
      } else {
        // Fallback: use folderId as driveId
        setDriveId(folderId);
        setCurrentFolderId(null);
        fetchFiles(null, folderId, siteId);
      }
    } else if (folderPath?.includes('/items/')) {
      // Clicking on a folder within a drive - navigate into it
      // Path format: /drives/{drive_id}/items/{folder_id}
      setCurrentFolderId(folderId);
      fetchFiles(folderId, driveId, siteId);
    } else {
      // Fallback: assume it's a folder within current drive
      setCurrentFolderId(folderId);
      fetchFiles(folderId, driveId, siteId);
    }
  };

  const handleFileToggle = (fileId: string) => {
    const newSelected = new Set(selectedFiles);
    if (newSelected.has(fileId)) {
      newSelected.delete(fileId);
    } else {
      newSelected.add(fileId);
    }
    setSelectedFiles(newSelected);
    onFilesSelected?.(Array.from(newSelected));
  };

  const handleSelectAll = () => {
    if (!browseData) return;
    if (selectedFiles.size === browseData.files.length) {
      setSelectedFiles(new Set());
      onFilesSelected?.([]);
    } else {
      const allFileIds = new Set(browseData.files.map((f) => f.id));
      setSelectedFiles(allFileIds);
      onFilesSelected?.(Array.from(allFileIds));
    }
  };

  const handleUpload = async () => {
    if (selectedFiles.size === 0) {
      toast.error('Please select files to upload');
      return;
    }

    if (!driveId) {
      toast.error('Drive ID not found. Please browse files first.');
      return;
    }

    if (!collectionUuid) {
      toast.error('Collection ID not available. Please wait...');
      return;
    }

    setIsUploading(true);
    try {
      const response = await apiClient.post(
        `/file-upload/${sourceConnectionId}/upload-selected`,
        {
          file_ids: Array.from(selectedFiles),
          collection_id: collectionUuid,
          drive_id: driveId,
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }

      const result = await response.json();
      toast.success(
        `Uploaded ${result.successful} file(s) successfully. ${result.failed} failed.`
      );

      // Clear selection
      setSelectedFiles(new Set());
      onFilesSelected?.([]);
    } catch (error: any) {
      toast.error(error.message || 'Failed to upload files');
    } finally {
      setIsUploading(false);
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <Card className={cn(isDark && 'bg-gray-900 border-gray-700')}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Folder className="h-5 w-5" />
            Browse & Select Files
          </CardTitle>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchFiles(currentFolderId, driveId)}
              disabled={isLoading}
            >
              <RefreshCw className={cn('h-4 w-4', isLoading && 'animate-spin')} />
            </Button>
            {selectedFiles.size > 0 && (
              <Button
                size="default"
                onClick={handleUpload}
                disabled={isUploading}
                className="bg-primary hover:bg-primary/90"
              >
                {isUploading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Submit {selectedFiles.size} File{selectedFiles.size !== 1 ? 's' : ''}
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : browseData ? (
          <div className="space-y-4">
            {/* Breadcrumb */}
            {browseData.current_path && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setCurrentFolderId(null);
                    setDriveId(null);
                    setSiteId(null);
                    setBrowseLevel('sites');
                    fetchFiles(null, null, null);
                  }}
                >
                  <ChevronLeft className="h-4 w-4" />
                  {browseLevel === 'sites' ? 'Root' : 
                   browseLevel === 'drives' ? 'Back to Sites' : 
                   'Back to Document Libraries'}
                </Button>
                {browseData.current_path !== '/' && (
                  <>
                    <ChevronRight className="h-4 w-4" />
                    <span className="truncate">{browseData.current_path}</span>
                  </>
                )}
              </div>
            )}

            {/* Select All */}
            {browseData.files.length > 0 && (
              <div className="flex items-center gap-2 pb-2 border-b">
                <Checkbox
                  checked={selectedFiles.size === browseData.files.length && browseData.files.length > 0}
                  onCheckedChange={handleSelectAll}
                />
                <span className="text-sm font-medium">
                  Select All ({browseData.files.length} files)
                </span>
              </div>
            )}

            {/* Folders (Sites, Drives, or Folders) */}
            {browseData.folders.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-sm font-medium text-muted-foreground">
                  {browseLevel === 'sites' ? 'SharePoint Sites' : 
                   browseLevel === 'drives' ? 'Document Libraries' : 
                   'Folders'}
                </h3>
                {browseData.folders.map((folder) => (
                  <Button
                    key={folder.id}
                    variant="ghost"
                    className="w-full justify-start"
                    onClick={() => handleFolderClick(folder.id, folder.path)}
                  >
                    <Folder className="h-4 w-4 mr-2" />
                    {folder.name}
                    <ChevronRight className="h-4 w-4 ml-auto" />
                  </Button>
                ))}
              </div>
            )}

            {/* Files */}
            {browseData.files.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-muted-foreground">
                    Document Files ({browseData.files.length})
                  </h3>
                  <span className="text-xs text-muted-foreground">
                    Only document files are shown (.PDF, .DOC, .XLS, .PPT, etc.)
                  </span>
                </div>
                <div className="space-y-1 max-h-96 overflow-y-auto">
                  {browseData.files.map((file) => {
                    const ext = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
                    const isSelected = selectedFiles.has(file.id);
                    return (
                      <div
                        key={file.id}
                        className={cn(
                          'flex items-center gap-3 p-3 rounded-md border transition-colors',
                          isSelected 
                            ? 'bg-primary/10 border-primary' 
                            : 'hover:bg-muted/50 border-transparent',
                          isDark && (isSelected ? 'bg-primary/20' : 'hover:bg-gray-800')
                        )}
                      >
                        <Checkbox
                          checked={isSelected}
                          onCheckedChange={() => handleFileToggle(file.id)}
                        />
                        <div className={cn(
                          'flex items-center justify-center w-10 h-10 rounded bg-muted',
                          isSelected && 'bg-primary/20'
                        )}>
                          <File className={cn(
                            'h-5 w-5',
                            isSelected ? 'text-primary' : 'text-muted-foreground'
                          )} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <div className="text-sm font-medium truncate">{file.name}</div>
                            {ext && (
                              <span className="text-xs px-1.5 py-0.5 rounded bg-muted text-muted-foreground">
                                {ext.toUpperCase()}
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {formatFileSize(file.size)}
                            {file.modified_at && ` • ${new Date(file.modified_at).toLocaleDateString()}`}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {browseData.files.length === 0 && browseData.folders.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                No files or folders found
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            Click refresh to browse files
          </div>
        )}
      </CardContent>
    </Card>
  );
}

