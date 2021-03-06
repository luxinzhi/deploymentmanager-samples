# Copyright 2015 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Creates an multiple compies of a VM based on spec."""
import copy
import common
import default
import vm_instance

# Properties for this component, also look at the vm_instance properties
VM_COPIES = default.VM_COPIES
ENDPOINT_NAME = default.ENDPOINT_NAME


# The optional and mandatory fields are the same as a vm_instance
def GenerateMultipleComputeVMs(context):
  """Generates multiple VMs that are copies of a single VM spec."""
  prop = context.properties
  if VM_COPIES not in prop:
    raise common.Error('%s property is needed for multiple VM generation' %
                       VM_COPIES)
  use_endpoint = ENDPOINT_NAME in prop
  n_of_copies = prop[VM_COPIES]
  resources = []
  new_disks = []
  for idx in range(1, n_of_copies + 1):
    ctx = copy.deepcopy(context)
    idx_prop = ctx.properties
    ctx.env[default.NAME] += AddIdx(idx)
    # Do something with the instance name and with the disk names
    disk_prefix = ctx.env[default.NAME]
    if default.INSTANCE_NAME in idx_prop:
      idx_prop[default.INSTANCE_NAME] += AddIdx(idx)
      disk_prefix = idx_prop[default.INSTANCE_NAME]
    if default.DISKS in idx_prop:
      # Modifies the disks in idx_prop to have a unique name
      # Adding the vm extension to match the final hostname
      NameTheDisks(idx_prop[default.DISKS], disk_prefix)
    if use_endpoint:
      idx_prop[ENDPOINT_NAME] += AddIdx(idx)
    resources += vm_instance.GenerateComputeVM(ctx)
    resources += vm_instance.AddServiceEndpointIfNeeded(ctx)
    new_disks += common.AddDiskResourcesIfNeeded(ctx)
  AddDisksToContext(context, new_disks)
  return resources


def AddIdx(idx):
  """Adds index value to a string for auto name generation."""
  return '-%s' % str(idx)


def NameTheDisks(disks, disk_prefix):
  """Loops through disk list and rename its named properties."""
  for disk in disks:
    if default.DISK_NAME in disk:
      disk[default.DISK_NAME] = disk_prefix + '-' + disk[default.DISK_NAME]
    if default.DEVICE_NAME in disk:
      disk[default.DEVICE_NAME] = disk_prefix + '-' + disk[default.DEVICE_NAME]


def AddDisksToContext(context, new_disks):
  """Makes the context aware of the disks that need to be created."""
  # This method will modify properties if needed.
  prop = context.properties
  if new_disks:
    disk_resources = prop.setdefault(default.DISK_RESOURCES, list())
    disk_resources.extend(new_disks)


def GenerateResourceList(context):
  """Returns list of resources generated by this module."""
  resources = GenerateMultipleComputeVMs(context)
  resources += common.AddDiskResourcesIfNeeded(context)
  return resources


@common.FormatErrorsDec
def GenerateConfig(context):
  """Generates YAML resource configuration."""
  return common.MakeResource(GenerateResourceList(context))
